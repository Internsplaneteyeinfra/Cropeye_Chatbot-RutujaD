# Irrigation Schedule: Frontend vs Backend Alignment

## 1. Frontend Logic (IrrigationSchedule.tsx)

### Data sources
- **ET (today):** From `POST https://dev-field.cropeye.ai/plots/{plotName}/compute-et/` with `plot_name`, `start_date`, `end_date`. Uses `data.et_24hr ?? data.ET_mean_mm_per_day ?? data.et ?? 0`.
- **ET (days 2–7):** Not from API. Uses **generateAdjustedET(baseEt)** – a seeded pseudo-random variation so different plots get different Low/Medium patterns. Seed = sum of `plotName` char codes + current day of month.
- **Rainfall (today):** From `GET https://dev-weather.cropeye.ai/current-weather?lat=&lon=` → `precip_mm`.
- **Rainfall (days 2–7):** From `GET https://dev-weather.cropeye.ai/forecast?lat=&lon=` → `data[i].precipitation` (string like `"0.0 mm"`), parsed via `extractNumericValue()`.

### ETO classification (getETRange)
- **Low:**  `etValue <= 3.0`
- **Medium:** `etValue <= 5.5`
- **High:**  `etValue > 5.5`

### Net ET
- `netEt = max(0, ET - rainfall)` (same for today and forecast days).

### Water required (L/acre)
- `waterRequired = round(netEt * Kc * 0.94 * 4046.86)`
- Constants: efficiency = 0.94, 1 acre = 4046.86 m².

### Flood time (when irrigation type is flood)
- Pipe diameter (m) = `pipeWidthInches * 0.0254`
- Pipe area (m²) = `π * (diameter/2)²`
- Base velocity (m/s) = `clamp(motorHp * 0.45, 0.75, 2.5)`
- Friction factor = if `distanceMotorToPlot` > 0: `max(0.5, 1 - (distance/100)*0.05)` else 1
- Effective velocity = base velocity × friction factor
- Flow (L/h) = pipe area × effective velocity × 3600 × 1000
- **Flood time (hours)** = `waterRequired / flowRateLitersPerHour`
- Display: `formatTimeHrsMins(hours)` → `"0 hrs 41 mins"` (hours floored, minutes rounded).

### generateAdjustedET (days 2–7)
- Seed from `plotName` (sum of char codes) + current date’s day of month.
- Seeded RNG: `(seed * 9301 + 49297) % 233280` then divide by 233280.
- Picks 2 or 3 “medium” days out of 0..5 at random (with that seed).
- For each of 6 days, if base ET is Low (≤3): medium days get ET in 3.2–5.0, others 2.0–2.9; if Medium (≤5.5): medium days 3.5–5.0, others 2.3–3.0; if High: mix of High/Medium/Low.
- Applies ±5% variation and rounds to 1 decimal; minimum 1.5.

---

## 2. Backend Logic (Before Alignment)

### Data sources
- **ET:** From `get_evapotranspiration(plot_id)` → `ET_mean_mm_per_day` or `et_24hr` or `et`.
- **ET (days 2–7):** Same `base_et` for all days (no variation).
- **Rainfall (today):** `get_current_weather(plot_id)` → `precip_mm`.
- **Rainfall (days 2–7):** `get_weather_forecast(plot_id)` → `data[i].precip_mm`. Forecast API may actually return `precipitation` (e.g. `"0.0 mm"`), so numeric parsing was missing.

### Calculations
- Net ET and water required use the **same formula** as frontend: `net_et = max(0, et - rainfall)`, `water_required = round(net_et * kc * 0.94 * 4046.86)`.

### Missing in backend
- No ETO **classification** (Low/Medium/High).
- No **adjusted ET** for days 2–7 (flat base_et).
- No **flood time**.
- Forecast rainfall not parsed from `precipitation` string.
- Schedule output lacked `et_range` and `flood_time`; keys differed (`evapotranspiration` vs frontend’s displayed ET, `water_required_liters` vs `waterRequired`).

---

## 3. Differences Summary

| Aspect              | Frontend                          | Backend (before)                    |
|---------------------|-----------------------------------|-------------------------------------|
| ET for days 2–7     | generateAdjustedET(baseEt) seeded | Same base_et every day              |
| ETO display         | Low / Medium / High               | Not computed                        |
| Rainfall forecast   | `data[i].precipitation` parsed    | `data[i].precip_mm` only            |
| Water formula       | netEt × Kc × 0.94 × 4046.86       | Same                                |
| Flood time          | Computed from motor/pipe/distance | Not computed                        |
| Output shape        | date, etRange, rainfall, waterRequired, time | date, evapotranspiration, rainfall, water_required_liters, no time |

---

## 4. Backend Changes for Alignment

1. **ET range:** Implement `get_et_range(et)` → "Low" | "Medium" | "High" with thresholds 3.0 and 5.5.
2. **Adjusted ET:** Port `generateAdjustedET` to Python with same seed (plot_id + day of month) and same RNG and day-selection logic so days 2–7 match frontend.
3. **Rainfall:** For today use `precip_mm` or parse `precipitation`; for forecast use `precip_mm` if present else parse `precipitation` (e.g. `"0.0 mm"` → 0.0).
4. **Flood time:** Add optional params `motor_hp`, `pipe_width_inches`, `distance_motor_to_plot_m` to `build()`. When provided, use the same formula as frontend and return `flood_time` string (e.g. `"0 hrs 41 mins"`). When not provided, return `null` or `"N/A"`.
5. **Schedule output:** Each day includes: `date`, `is_today`, `et_value`, `et_range`, `rainfall_mm`, `water_required_liters`, `flood_time` (and optionally `net_et`) so the chatbot can return the same structure as the frontend table.

After these changes, the chatbot’s 7-day irrigation schedule matches the frontend’s calculation and presentation (same ETO levels, water required, and flood time when motor/pipe/distance are available).

---

## 5. Chatbot schedule output (aligned with frontend table)

Each day in `schedule_7_day` now has:

| Field                   | Type    | Example / meaning                    |
|-------------------------|--------|--------------------------------------|
| `date`                  | string | `"11 Feb"` (same as frontend)        |
| `is_today`              | bool   | `true` for first day                 |
| `et_value`              | number | ET in mm/day (1 decimal)             |
| `et_range`              | string | `"Low"` \| `"Medium"` \| `"High"`    |
| `rainfall_mm`           | number | Rainfall in mm (1 decimal)            |
| `net_et`                | number | ET − rainfall (2 decimals)            |
| `water_required_liters` | int    | Rounded L/acre                       |
| `flood_time`            | string | `"0 hrs 41 mins"` or `"N/A"`         |

The response generator receives this analysis and can format the reply to list the same columns as the frontend: **Date**, **ETO**, **Rainfall (mm)**, **Water req. (L)**, **Flood time**.

---

## 6. Exact numeric match (APIs)

For the chatbot to return **exactly** the same numbers as the frontend for a given plot and day:

- **ET:** The chatbot should use the same ET API and parameters as the frontend (e.g. same base URL and, if the frontend uses POST with `plot_name`, `start_date`, `end_date`, the backend may need to call the same endpoint with the same body). If the chatbot uses a different ET endpoint, ensure it returns the same `et_24hr` / `ET_mean_mm_per_day` for that plot.
- **Rainfall:** Use the same current-weather and forecast APIs and the same lat/lon or plot_id so today and forecast rainfall match. The backend now parses both `precip_mm` and `precipitation` (e.g. `"0.0 mm"`) for compatibility.
- **Kc:** Pass `kc` from context (e.g. from crop stage) when available; otherwise the backend uses 0.3 (frontend default).
- **Flood time:** Pass `motor_hp`, `pipe_width_inches`, and optionally `distance_motor_to_plot_m` in context (e.g. from farm/profile) so flood time is computed; otherwise the schedule shows `"N/A"`.
