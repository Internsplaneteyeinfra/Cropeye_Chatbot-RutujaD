# unified_agent.py
from app.prompts.unified_prompt import UNIFIED_SYSTEM_PROMPT
from app.utils.json_utils import safe_json
from app.config import llm
from app.utils.lang_detect import detect_lang
import json

def unified_agent(state: dict) -> dict:
    """
    Unified agent that handles both intent detection and response generation.
    - If intent is not set: performs intent detection and entity extraction
    - If intent is already set: generates final response
    """
    
    user_message = state.get("user_message", "")
    existing_intent = state.get("intent")
    language = state.get("user_language")
    analysis = state.get("analysis", {})
    context = state.get("context", {})
    history = state.get("short_memory", []) or []
    
    # Detect language if not set
    if not language:
        language = detect_lang(user_message)
        state["user_language"] = language
    
    # Build conversation history
    history_text = ""
    last_intent = None
    for h in history:
        history_text += f"{h.get('role', '')}: {h.get('message', '')}\n"
        if h.get("intent"):
            last_intent = h["intent"]
    
    # ---------- FAST GREETING SHORT-CIRCUIT (before any LLM calls) ----------
    if not existing_intent:
        message_lower = user_message.lower().strip()
        greeting_responses = {
            "hi": "Hello! How can I help you with your farm today?",
            "hello": "Hello! How can I help you with your farm today?",
            "hey": "Hey! How can I assist you with your crops?",
            "namaste": "नमस्ते! मी तुमच्या शेतासाठी कशी मदत करू शकतो?",
            "नमस्ते": "नमस्ते! मी तुमच्या शेतासाठी कशी मदत करू शकतो?",
            "thanks": "You're welcome! Feel free to ask if you need anything else.",
            "thank you": "You're welcome! Feel free to ask if you need anything else.",
            "bye": "Goodbye! Take care of your crops!",
            "goodbye": "Goodbye! Take care of your crops!",
            "ok": "Got it! Anything else you'd like to know?",
            "okay": "Got it! Anything else you'd like to know?",
            "yes": "Understood. What would you like to know?",
            "no": "No problem. How can I help you?",
            "help": "I can help you with soil analysis, weather forecasts, irrigation advice, fertilizer recommendations, pest detection, and crop monitoring. What do you need?",
            "who are you": "I'm CropEye, your agriculture intelligence assistant. I help farmers with crop management, soil analysis, weather forecasts, and farming advice."
        }
        
        # Direct match
        if message_lower in greeting_responses:
            state["intent"] = "general_explanation"
            state["final_response"] = greeting_responses[message_lower]
            state["user_language"] = language or "en"
            return state
        
        # Partial match for multi-word greetings
        for key, response in greeting_responses.items():
            if key in message_lower and len(message_lower.split()) <= 3:
                state["intent"] = "general_explanation"
                state["final_response"] = response
                state["user_language"] = language or "en"
                return state

    # MODE 1: Intent Detection (when intent is not set)
    if not existing_intent:
        # Build intent detection prompt
        intent_prompt = f"""{UNIFIED_SYSTEM_PROMPT}

TASK: Intent Detection and Entity Extraction

You must identify the farmer's intent and extract relevant entities.
DO NOT answer the question yet.

Conversation history:
{history_text}

--------------------------------
INTENT SELECTION RULES
--------------------------------

1. dashboard_summary → overall farm condition, crop status, yield, stress, sugar, biomass, indices
2. map_view → spatial/visual field maps
3. soil_moisture → soil wetness level or trend (NOT irrigation advice)
4. irrigation_advice → irrigation decision/action
5. irrigation_schedule → multi-day water plan
6. soil_analysis → soil quality, nutrients, fertility, NPK, soil report
7. weather_forecast → weather, rain, temp, humidity, wind
8. fertilizer_advice → fertilizer usage, NPK, schedule, videos
9. pest_risk → pests, disease, weeds
10. general_explanation → greeting/help/off-topic (ONLY if no agriculture meaning)

RULE: If ANY farming meaning exists → NEVER use general_explanation.

--------------------------------
ENTITY EXTRACTION
--------------------------------
Extract only if present:
- date: tomorrow / उद्या / etc (or null)
- parameter: pH / N / P / K etc (or null)
- query_type: based on intent mapping (or null)

--------------------------------
QUERY_TYPE MAPPING
--------------------------------
dashboard_summary → crop_status_check, yield_info, sugar_content_check, stress_check, biomass_check, indices_check
map_view → soil_moisture_map, water_uptake_map, growth_map, pest_map
soil_moisture → soil_moisture_current, soil_moisture_trend
irrigation_advice → irrigate_today, water_required
irrigation_schedule → 7_day_schedule
fertilizer_advice → video_resources, fertilizer_schedule, fertilizer_soil_npk_requirements

--------------------------------
OUTPUT FORMAT (JSON ONLY)
--------------------------------
{{
  "intent": "intent_name",
  "entities": {{
    "date": null,
    "parameter": null,
    "query_type": null
  }}
}}

Farmer message:
"{user_message}"
"""
        
        try:
            response = llm.invoke(intent_prompt)
            
            # Handle different response formats
            content = ""
            if hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'text'):
                content = response.text
            elif isinstance(response, str):
                content = response
            else:
                content = str(response)
                
            # ---------- DISABLE VERBOSE LOGGING FOR PERFORMANCE ----------
            # print("RAW LLM RESPONSE (INTENT):", content)
            
            result = safe_json(content)
            intent = result.get("intent")
            entities = result.get("entities")
            
            if not intent:
                intent = last_intent if last_intent else "general_explanation"
            
            state["intent"] = intent
            state["entities"] = entities if isinstance(entities, dict) else {}
            
            # If intent is general_explanation, generate response immediately
            if intent == "general_explanation":
                # Continue to response generation below
                existing_intent = intent
            else:
                return state
            
        except Exception as e:
            print(f"UNIFIED_AGENT_ERROR (INTENT): {str(e)}")
            state["intent"] = last_intent if last_intent else "general_explanation"
            state["entities"] = {}
            
            # If it's general_explanation, generate response immediately
            if state["intent"] == "general_explanation":
                existing_intent = state["intent"]
            else:
                return state
    
    # MODE 2: Response Generation (when intent is already set)
    # Use existing_intent if available, otherwise get from state
    response_intent = existing_intent or state.get("intent", "general_explanation")
    
    # Build response generation prompt
    analysis_str = "No analysis data available"
    if analysis:
        try:
            if isinstance(analysis, dict):
                analysis_str = json.dumps(analysis, indent=2, ensure_ascii=False)
            else:
                analysis_str = str(analysis)
        except Exception:
            analysis_str = str(analysis)
    
    # ---------- REMOVE cached_data FOR general_explanation TO REDUCE PROMPT SIZE ----------
    context_str = "No context available"
    if context:
        try:
            # For general_explanation, only keep minimal context (no cached_data)
            if response_intent == "general_explanation":
                minimal_context = {
                    "plot_id": context.get("plot_id"),
                    "user_id": context.get("user_id")
                }
                context_str = json.dumps(minimal_context, indent=2, ensure_ascii=False)
            else:
                context_str = json.dumps(context, indent=2, ensure_ascii=False)
        except Exception:
            context_str = str(context)
    
    response_prompt = f"""{UNIFIED_SYSTEM_PROMPT}

TASK: Generate Final Response

You must generate a natural, farmer-friendly reply in the same language as the user.
This response will be used for both text and voice interfaces.

Context:
- User intent: {response_intent}
- User language: {language}
- Conversation history:
{history_text}

Farm Context:
{context_str}

Analysis Data:
{analysis_str}

--------------------------------
RESPONSE GENERATION RULES
--------------------------------

PRIORITY:
1. If intent is greeting/general_explanation → reply greeting only, no data mention
2. Respond in SAME language as user ({language})
3. Maximum 3-4 short lines
4. Use ONLY provided analysis and context
5. DO NOT invent, assume, or guess any data
6. Speak like a real agronomist helping a farmer
7. Natural spoken tone (works for both text and voice)
8. No technical jargon, no UI references
9. No system details, APIs, satellites, models, calculations
10. Include numeric values with clear units when present
11. Add meaning to values (good / low / high / improving / stable)
12. If data missing → say naturally it is unavailable
13. For spatial queries → describe WHERE differences occur
14. For partial data → mention uncertainty naturally

--------------------------------
DOMAIN-SPECIFIC INTERPRETATION
--------------------------------

DASHBOARD: Interpret farm metrics meaning naturally.
MAP: Describe spatial variation only. Never recommend actions.
SOIL MOISTURE: Use value vs optimal range (below→low, within→good, above→high)
WEATHER: Interpret using temp/rain/wind/humidity values only. Explain from tomorrow.
FERTILIZER: Positive→needed, Negative→excess, Zero→balanced
PEST + CROP HEALTH: Include growth stage, health, pests, disease, weeds, action if needed
IRRIGATION: Multi-day→schedule, Decision→advice

--------------------------------
OUTPUT
--------------------------------
Return ONLY the final answer text.
No JSON, no explanation, no metadata, no intent label.

User message:
"{user_message}"
"""
    
    try:
        response = llm.invoke(response_prompt)
        
        # Handle different response formats
        content = ""
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'text'):
            content = response.text
        elif isinstance(response, str):
            content = response
        else:
            content = str(response)
        
        # Clean up the response (remove any JSON markers if present)
        content = content.strip()
        if content.startswith("```"):
            # Remove markdown code blocks
            lines = content.split("\n")
            content = "\n".join([l for l in lines if not l.strip().startswith("```")])
        
        state["final_response"] = content.strip()
        
    except Exception as e:
        print(f"UNIFIED_AGENT_ERROR (RESPONSE): {str(e)}")
        state["final_response"] = "I'm having trouble right now. Please try again."
    
    return state
