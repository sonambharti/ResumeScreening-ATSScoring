import os
import sys
from dotenv import load_dotenv
from resume_ats_agent.config.settings import settings
from resume_ats_agent.core.logger import logger

def main():
    # Load configurations
    load_dotenv()
    
    # Create persistent directories for data and logging
    os.makedirs("./data", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)
    os.makedirs(settings.vector_db_dir, exist_ok=True)
    
    logger.info("Starting Resume Screening & ATS Scoring Platform...")
    
    # Warn user about missing API keys on startup if none found
    if not settings.openai_api_key and not settings.gemini_api_key:
        logger.warning(
            "No LLM API keys found in the environment. "
            "The application will launch, but you MUST provide an OpenAI or Gemini API key "
            "in the Settings tab before running analysis or chat."
        )
        
    try:
        from resume_ats_agent.ui.app import create_gradio_app
        app = create_gradio_app()
        
        # Launch Gradio server
        # On Hugging Face Spaces or Docker, we should bind to 0.0.0.0 so external requests are proxied properly.
        # Locally we can bind to 127.0.0.1 or 0.0.0.0. We default to 0.0.0.0 to cover all hosting models.
        server_name = os.getenv("GRADIO_SERVER_NAME", "0.0.0.0")
        server_port = int(os.getenv("GRADIO_SERVER_PORT", 7860))
        
        logger.info(f"Launching Gradio UI on {server_name}:{server_port}...")
        app.launch(server_name=server_name, server_port=server_port, share=False)
        
    except Exception as e:
        logger.critical(f"Platform failed to start due to an unhandled exception: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
