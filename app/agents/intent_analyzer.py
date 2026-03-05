# #intent_analyzer.py
# from app.prompts.intent_prompt import INTENT_PROMPT
# from app.utils.json_utils import safe_json
# from app.prompts.base_system_prompt import BASE_SYSTEM_PROMPT
# from app.config import llm
# from app.utils.lang_detect import detect_lang

# def intent_analyzer(state: dict) -> dict:
    
#     user_message = state.get("user_message", "")
#     state["user_language"] = detect_lang(user_message)
#     history = state.get("short_memory", []) or []

#     # Build conversation context
#     history_text = ""
#     last_intent = None

#     for h in history:
#         history_text += f"{h['role']}: {h['message']}"
#         if h.get("intent"):
#             last_intent = h["intent"]

#     prompt = ( BASE_SYSTEM_PROMPT +"Conversation history:\n" + history_text  + INTENT_PROMPT ).format(user_message=user_message)
    
#     try:
#         response = llm.invoke(prompt)
        
#         # Handle different response formats
#         content = ""
#         if hasattr(response, 'content'):
#             content = response.content
#         elif hasattr(response, 'text'):
#             content = response.text
#         elif isinstance(response, str):
#             content = response
#         else:
#             content = str(response)
            
#         print("RAW LLM RESPONSE:", content)

#         result = safe_json(content)        
#         intent = result.get("intent")
#         entities = result.get("entities")

#         if not intent:
#             intent = last_intent  

#         state["intent"] = intent
#         state["entities"] = entities if isinstance(entities, dict) else {}

#     except Exception as e:
#         print(f"INTENT_ANALYZER_ERROR: {str(e)}")
#         # state["intent"] = "general_explanation"
#         state["intent"] = last_intent  # reuse previous intent
#         state["entities"] = {}

#     return state