# unified_agent.py
# from app.prompts.unified_prompt import UNIFIED_SYSTEM_PROMPT
from app.prompts.intent_prompt import INTENT_SYSTEM_PROMPT
from app.prompts.response_prompt import RESPONSE_PROMPT
from app.utils.json_utils import safe_json
from app.config import llm
from app.utils.lang_detect import detect_lang
from app.utils.filter_analysis import filter_analysis_by_intent
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

    # analysis = state.get("analysis", {})
    # filtered_analysis = filter_analysis_by_intent(
    #     existing_intent,
    #     analysis
    # )
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

    if not existing_intent:
      
        intent_prompt = f"""{INTENT_SYSTEM_PROMPT}
        Conversation history:
        {history_text}

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
                
          
            
            result = safe_json(content)
            intent = result.get("intent")
            print("\nDEBUG INTENT DETECTED:", intent)
            entities = result.get("entities")
            
            if not intent:
                intent = last_intent if last_intent else "general_explanation"
            
            state["intent"] = intent
            state["entities"] = entities if isinstance(entities, dict) else {}

            cached_data = state.get("context", {}).get("cached_data", {})
            print("\nDEBUG CACHED DATA KEYS:", list(cached_data.keys()))
            
            filtered = filter_analysis_by_intent(intent, cached_data)

            # Extract only useful context (NOT cached_data)
            context_for_analysis = {
                "plot_id": context.get("plot_id"),
                "plantation_date": context.get("plantation_date"),
                "crop_stage": context.get("crop_stage"),
                "days_since_plantation": context.get("days_since_plantation"),
                "plantation_type": context.get("plantation_type"),
                "planting_method": context.get("planting_method"),
                "kc": context.get("kc"),
                "lat": context.get("lat"),
                "lon": context.get("lon")
            }

            analysis_payload = {
                "context": context_for_analysis,
                "data": filtered
            }

            # print("\nDEBUG FILTERED DATA KEYS:", list(filtered.keys()))
            state["analysis"] = analysis_payload
            analysis = analysis_payload
            
            # REMOVE large cached data after filtering
            state["context"].pop("cached_data", None)


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
    
    response_intent = existing_intent or state.get("intent", "general_explanation")
    
    analysis_str = "No analysis data available"
    if analysis:
        try:
            # if isinstance(filtered_analysis, dict):
            #     analysis_str = json.dumps(filtered_analysis, indent=2, ensure_ascii=False)
            if isinstance(analysis, dict):
                analysis_str = json.dumps(analysis, indent=2, ensure_ascii=False)
            else:
                analysis_str = str(analysis)
        except Exception:
            analysis_str = str(analysis)
    
    # ---------- REMOVE cached_data FOR general_explanation TO REDUCE PROMPT SIZE ----------
    # context_str = "No context available"
    # if context:
    #     try:
    #         if response_intent == "general_explanation":
    #             minimal_context = {
    #                 "plot_id": context.get("plot_id"),
    #                 "user_id": context.get("user_id")
    #             }
    #             context_str = json.dumps(minimal_context, indent=2, ensure_ascii=False)
    #         else:
    #             context_str = json.dumps(context, indent=2, ensure_ascii=False)
    #     except Exception:
    #         context_str = str(context)
    
    response_prompt = f"""{RESPONSE_PROMPT}
        User message: "{user_message}"
        Analysis: {analysis_str}
        """
    
    try:
        response = llm.invoke(response_prompt)

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
