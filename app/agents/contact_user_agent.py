from typing import Any, Dict, Optional

from app.memory.redis_manager import redis_manager


def _extract_field_officer_info(plot_id: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Best-effort extraction of field officer contact info from cached public_plots.
    Uses ONLY cached Redis data – never calls external APIs.
    """
    if not plot_id:
        return None

    try:
        profile_data = redis_manager.get("public_plots") or {}
    except Exception as e:
        print(f"[contact_user_agent] Error reading public_plots from cache: {e}")
        return None

    plots = profile_data.get("results", [])
    target_plot: Optional[Dict[str, Any]] = None

    for plot in plots:
        pid = plot.get("fastapi_plot_id")
        if str(pid) == str(plot_id):
            target_plot = plot
            break

    if not target_plot:
        return None

    fo_data = (
        target_plot.get("field_officer")
        or target_plot.get("field_officers")
        or target_plot.get("field_officer_details")
    )

    if not fo_data:
        return None

    if isinstance(fo_data, list) and fo_data:
        fo_data = fo_data[0]

    if not isinstance(fo_data, dict):
        return None

    name = (
        fo_data.get("full_name")
        or fo_data.get("username")
        or "your Field Officer"
    )

    return {
        "name": name,
    }

async def contact_user_agent(state: dict) -> dict:

    plot_id = state.get("context", {}).get("plot_id")
    officer = _extract_field_officer_info(plot_id)

    if officer:

        message = (
            f"You can contact your Field Officer **{officer['name']}** from the Contact User page.\n\n"
            "Follow these steps:\n"
            "1. Open your **Dashboard**.\n"
            "2. Click **Contactuser** in the left menu.\n"
            "3. In the **Field Officer** section select the officer.\n"
            "4. On the right side open the **Send Message** panel.\n"
            "5. Type your message and click **Send**.\n\n"
            "Your message will reach the Field Officer."
        )

    else:

        message = (
            "You can contact your Field Officer, Manager, or Owner from the **Contact User** page.\n\n"
            "Follow these steps:\n"
            "1. Open your **Dashboard**.\n"
            "2. Click **Contactuser** in the left menu.\n"
            "3. Select **Field Officer**, **Manager**, or **Owner**.\n"
            "4. Use the **Send Message** box on the right side.\n"
            "5. Type your message and click **Send**.\n\n"
            "This will send your message directly to them."
        )

    state["analysis"] = {
        "contact_user": {
            "field_officer_available": bool(officer)
        }
    }

    state["final_response"] = message

    return state