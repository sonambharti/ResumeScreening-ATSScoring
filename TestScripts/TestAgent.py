import os
import sys
from dotenv import load_dotenv
# Add project root to path
sys.path.append(r"e:\Assignments\Resume Screening - ATS Scoring Platform")
from resume_ats_agent.config.settings import settings
from resume_ats_agent.facade import ScreeningSystemFacade
from resume_ats_agent.core.logger import logger
def test():
    load_dotenv()
    print("Default LLM Provider:", settings.default_llm_provider)
    print("Default Model Name:", settings.default_model_name)
    print("OpenAI Key Configured:", bool(settings.openai_api_key))
    print("Gemini Key Configured:", bool(settings.gemini_api_key))
    print("Groq Key Configured:", bool(settings.groq_api_key))
    
    facade = ScreeningSystemFacade()
    
    # Mock some data if needed, or check initialization
    try:
        print("\nAttempting to initialize the ReAct Agent...")
        facade.agent_manager.initialize_agent()
        print("ReAct Agent compilation SUCCESSFUL!")
        
        print("\nAttempting to run a test message...")
        response = facade.chat_with_recruiter_agent("Hello, who are you?", [])
        print("Agent Response:\n", response)
    except Exception as e:
        import traceback
        print("\n--- ERROR CAUGHT ---")
        traceback.print_exc()
if __name__ == "__main__":
    test()
