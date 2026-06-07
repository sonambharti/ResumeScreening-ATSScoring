import os
import sys
# Add project root to path
sys.path.append(r"e:\Assignments\Resume Screening - ATS Scoring Platform")
from resume_ats_agent.config.settings import settings
from resume_ats_agent.facade import ScreeningSystemFacade
def test_groq_compilation():
    print("=== TEST 1: Test Groq Compilation ===")
    settings.default_llm_provider = "groq"
    settings.default_model_name = "llama-3.3-70b-versatile"
    settings.groq_api_key = "gsk_mock_key_here_12345678901234567890"
    
    facade = ScreeningSystemFacade()
    try:
        facade.agent_manager.initialize_agent()
        print("ReAct Agent compiled with Groq SUCCESSFUL!")
    except Exception as e:
        print("ReAct Agent compiled with Groq FAILED:", str(e))
def test_chatbot_history_formats():
    print("\n=== TEST 2: Test Chatbot History Formats ===")
    settings.default_llm_provider = "openai"
    settings.default_model_name = "gpt-4o"
    settings.openai_api_key = "sk-mock-key-here-12345678901234567890"
    
    facade = ScreeningSystemFacade()
    
    # Compile agent
    facade.agent_manager.initialize_agent()
    
    # 1. Test dict-based history (Gradio 4/5 Messages API)
    dict_history = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    print("Testing dict-based history...")
    try:
        # Should initiate the chain and output invalid key error rather than a packing/ValueError
        res = facade.chat_with_recruiter_agent("Who are you?", dict_history)
        print("Result (dict-based):", res)
    except Exception as e:
        print("Failed on dict-based history:", str(e))
        
    # 2. Test tuple-based history (Legacy Gradio)
    tuple_history = [
        ("Hello", "Hi there!")
    ]
    print("\nTesting tuple-based history...")
    try:
        res = facade.chat_with_recruiter_agent("Who are you?", tuple_history)
        print("Result (tuple-based):", res)
    except Exception as e:
        print("Failed on tuple-based history:", str(e))
if __name__ == "__main__":
    test_groq_compilation()
    test_chatbot_history_formats()
