# unified_agent.py
# from app.prompts.unified_prompt import UNIFIED_SYSTEM_PROMPT
from app.utils.json_utils import safe_json
from app.config import llm
from app.utils.lang_detect import detect_lang
import json
from app.prompts.intent_prompt import INTENT_SYSTEM_PROMPT
from app.prompts.response_prompt import RESPONSE_PROMPT
from app.utils.cache_filter import filter_cache_by_intent
from app.utils.analysis_compressor import compress_analysis
import time

from langchain_core.messages import AIMessage

def unified_agent(state: dict) -> dict:
    """
    Unified agent that handles both intent detection and response generation.
    - If intent is not set: performs intent detection and entity extraction
    - If intent is already set: generates final response
    """
    messages = state["messages"]
    history_text = ""
    for m in messages[:-1]:  # exclude latest message
        role = "Farmer" if m.__class__.__name__ == "HumanMessage" else "Assistant"
        history_text += f"{role}: {m.content}\n"

    user_message = messages[-1].content

    # user_message = state.get("user_message", "")
    existing_intent = state.get("intent")
    language = state.get("user_language")
    analysis = state.get("analysis", {})
    print("\n===== ANALYSIS DATA =====")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    print("=========================\n")
    context = state.get("context", {})

    # ---------- LOAD CONVERSATION STATE ----------
    # conv_state = state.get("conversation_state")
    # if conv_state and existing_intent is None:
    #     state["intent"] = conv_state.get("intent")
    #     state["entities"] = conv_state.get("entities", {})
    #     existing_intent = state["intent"]
  
    if not language:
        language = detect_lang(user_message)
        state["user_language"] = language
    
    # Build conversation history
    # history_text = ""
    # last_intent = None
    # for h in history:
    #     history_text += f"{h.get('role', '')}: {h.get('message', '')}\n"
    #     if h.get("intent"):
    #         last_intent = h["intent"]
    
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
        # Get previous conversation context for better intent detection
        conv_state = state.get("conversation_state") or {}
        previous_intent = conv_state.get("intent")
        previous_entities = conv_state.get("entities", {})
        
        # ========== DEBUG: Intent Detection Context ==========
        print("\n" + "="*80)
        print("🔍 [DEBUG] INTENT DETECTION - CONTEXT ANALYSIS")
        print("="*80)
        print(f"💬 Current user message: {user_message}")
        print(f"📜 Conversation history length: {len(history_text)} characters")
        print(f"🎯 Previous intent from conversation_state: {previous_intent or 'None (first message)'}")
        print(f"🏷️  Previous entities: {json.dumps(previous_entities, ensure_ascii=False)}")
        if history_text:
            print(f"\n📜 Conversation history preview:")
            print(history_text[:300] + "..." if len(history_text) > 300 else history_text)
        print("="*80 + "\n")
        # ====================================================
        
        # Build context-aware intent detection prompt (concise)
        context_info = ""
        if previous_intent:
            context_info = f"""
PREVIOUS: intent={previous_intent}, entities={json.dumps(previous_entities, ensure_ascii=False)}
- Short/ambiguous messages → likely same intent
- New concept mentioned → choose matching intent
"""

        # Build intent detection prompt (concise)
        intent_prompt = f"""{INTENT_SYSTEM_PROMPT}
{context_info}
HISTORY:
{history_text}

MESSAGE: "{user_message}"
"""
        
        # ========== DEBUG: Show Prompt Sent to LLM ==========
        print("\n" + "="*80)
        print("🔍 [DEBUG] INTENT DETECTION PROMPT SENT TO LLM")
        print("="*80)
        print(intent_prompt)
        print("="*80 + "\n")
        # =====================================================
        
        try:
            start = time.perf_counter()
            response = llm.invoke(intent_prompt)
            print(f"⏱ Intent LLM time: {time.perf_counter() - start:.3f}s")
            
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
            
            # ========== DEBUG: LLM Raw Response ==========
            print("\n" + "="*80)
            print("🔍 [DEBUG] LLM RAW RESPONSE (INTENT DETECTION)")
            print("="*80)
            print(content)
            print("="*80 + "\n")
            # ============================================
            
            result = safe_json(content)
            
            intent = result.get("intent")
            entities = result.get("entities")
            
            if not intent:
                # intent = last_intent if last_intent else "general_explanation"
                intent = intent or "general_explanation"
            
            # ========== DEBUG: Intent Detection Result ==========
            print("\n" + "="*80)
            print("🔍 [DEBUG] INTENT DETECTION RESULT")
            print("="*80)
            print(f"✅ Detected intent: {intent}")
            print(f"🏷️  Detected entities: {json.dumps(entities, ensure_ascii=False)}")
            if previous_intent:
                if intent == previous_intent:
                    print(f"✅ Intent MATCHED previous intent: {previous_intent}")
                else:
                    print(f"⚠️  Intent CHANGED from '{previous_intent}' → '{intent}'")
                    print(f"   Reason: LLM decided to change intent based on current message")
            else:
                print(f"ℹ️  First message - no previous intent to compare")
            print("="*80 + "\n")
            # ===================================================
            
            state["intent"] = intent

            # new_entities = entities if isinstance(entities, dict) else {}

            # conv_state = state.get("conversation_state")

            # # restore previous entities if new ones missing
            # if conv_state:
            #     prev_entities = conv_state.get("entities", {})

            #     for k, v in prev_entities.items():
            #         if not new_entities.get(k):
            #             new_entities[k] = v

            # state["entities"] = new_entities
            # # ---------- UPDATE CONVERSATION STATE ----------
            # # conv_state = state.get("conversation_state") or {}
            # conv_state["intent"] = state["intent"]
            # conv_state["entities"] = state["entities"]
            # state["conversation_state"] = conv_state
            
            new_entities = entities if isinstance(entities, dict) else {}

            # Get previous conversation state safely
            conv_state = state.get("conversation_state") or {}

            # Restore missing entities from previous turn
            prev_entities = conv_state.get("entities", {})

            for k, v in prev_entities.items():
                if not new_entities.get(k):
                    new_entities[k] = v

            state["entities"] = new_entities

            # ---------- UPDATE CONVERSATION STATE ----------
            conv_state["intent"] = state["intent"]
            conv_state["entities"] = state["entities"]

            state["conversation_state"] = conv_state
            
            # ========== DEBUG: Updated Conversation State ==========
            print("\n" + "="*80)
            print("🔍 [DEBUG] UPDATED CONVERSATION STATE (SAVED TO MEMORY)")
            print("="*80)
            print(f"💾 Intent saved: {conv_state.get('intent')}")
            print(f"💾 Entities saved: {json.dumps(conv_state.get('entities', {}), ensure_ascii=False)}")
            print(f"   (This will be available for the next user message)")
            print("="*80 + "\n")
            # ======================================================
            
            # If intent is general_explanation, generate response immediately
            if intent == "general_explanation":
                # Continue to response generation below
                existing_intent = intent
            else:
                return state
            
        except Exception as e:
            print(f"UNIFIED_AGENT_ERROR (INTENT): {str(e)}")
            # state["intent"] = last_intent if last_intent else "general_explanation"
            state["intent"] = "general_explanation"
            state["entities"] = {}
            
            # If it's general_explanation, generate response immediately
            if state["intent"] == "general_explanation":
                existing_intent = state["intent"]
            else:
                return state
    
    response_intent = existing_intent or state.get("intent", "general_explanation")
    
    # ========== DEBUG: Response Generation Phase ==========
    print("\n" + "="*80)
    print("🔍 [DEBUG] RESPONSE GENERATION PHASE")
    print("="*80)
    print(f"🎯 Intent for response: {response_intent}")
    print(f"💬 User message: {user_message}")
    print(f"📜 Conversation history length: {len(history_text)} characters")
    print("="*80 + "\n")
    # ====================================================

    # -------- FILTER CACHE BASED ON INTENT --------
    cached_data = context.get("cached_data")

    if cached_data:
        filtered_cache = filter_cache_by_intent(response_intent, cached_data)

        # remove None values
        filtered_cache = {k: v for k, v in filtered_cache.items() if v is not None}

        if filtered_cache:
            context["cached_data"] = filtered_cache
        else:
            context.pop("cached_data", None)


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
                print(f"CONTEXT SENT TO LLM: {context_str}")

            else:
                # context_str = json.dumps(context, indent=2, ensure_ascii=False)
                minimal_context = {
                    "plot_id": context.get("plot_id"),
                    "crop_stage": context.get("crop_stage"),
                    "plantation_date": context.get("plantation_date"),
                }
                context.pop("cached_data", None)
              
                # pass
                context_str = json.dumps(minimal_context, indent=2, ensure_ascii=False)
                print(f"FARM CONTEXT SENT TO LLM: {context_str}")

        except Exception:
            context_str = str(context)
    
    response_prompt = f"""{RESPONSE_PROMPT}
        User message: "{user_message}"
        context: {context_str}
        analysis: {analysis_str}
        """
    
    try:
        print("PROMPT LENGTH:", len(response_prompt))
        start = time.perf_counter()
        response = llm.invoke(response_prompt)
        print(f"⏱ LLM call took {time.perf_counter()-start:.3f}s")
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
        state["messages"].append(
            AIMessage(content=content.strip())
        )
        
    except Exception as e:
        print(f"UNIFIED_AGENT_ERROR (RESPONSE): {str(e)}")
        state["final_response"] = "I'm having trouble right now. Please try again."
    
    return state
