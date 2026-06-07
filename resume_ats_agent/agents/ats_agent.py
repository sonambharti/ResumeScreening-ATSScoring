from typing import List, Dict, Any, Callable
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from resume_ats_agent.config.settings import settings
from resume_ats_agent.core.exceptions import AgentExecutionError, ConfigurationError
from resume_ats_agent.core.logger import logger
from resume_ats_agent.agents.tools import create_screening_tools
from resume_ats_agent.rag.vector_store import VectorStoreManager
from resume_ats_agent.engine.scoring import ScoringEngine

class ATSAgentManager:
    """Manages the creation, configuration, and execution of the LangChain ReAct agent."""
    
    def __init__(
        self,
        vector_store: VectorStoreManager,
        scoring_engine: ScoringEngine,
        get_candidate_cache: Callable[[], Dict[str, Any]],
        get_active_jd: Callable[[], str]
    ):
        self.vector_store = vector_store
        self.scoring_engine = scoring_engine
        self.get_candidate_cache = get_candidate_cache
        self.get_active_jd = get_active_jd
        self.agent_executor = None
        
    def _get_llm(self, temperature: float = 0.0):
        provider = settings.default_llm_provider
        model_name = settings.default_model_name
        
        if provider == "openai":
            if not settings.openai_api_key:
                raise ConfigurationError(
                    "OpenAI API key is missing. Configure it in the Settings panel or your .env file."
                )
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(model=model_name, temperature=temperature, api_key=settings.openai_api_key)
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize OpenAI LLM: {str(e)}")
                
        elif provider in ["gemini", "google"]:
            if not settings.gemini_api_key:
                raise ConfigurationError(
                    "Gemini API key is missing. Configure it in the Settings panel or your .env file."
                )
            try:
                from langchain_google_genai import ChatGoogleGenAI
                return ChatGoogleGenAI(model=model_name, temperature=temperature, google_api_key=settings.gemini_api_key)
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize Gemini LLM: {str(e)}")
                
        elif provider == "groq":
            if not settings.groq_api_key:
                raise ConfigurationError(
                    "Groq API key is missing. Configure it in the Settings panel or your .env file."
                )
            try:
                from langchain_groq import ChatGroq
                return ChatGroq(model_name=model_name, temperature=temperature, api_key=settings.groq_api_key)
            except Exception as e:
                raise ConfigurationError(f"Failed to initialize Groq LLM: {str(e)}")
                
        else:
            raise ConfigurationError(f"Unsupported LLM provider '{provider}'.")

    def initialize_agent(self):
        """Assembles the LangChain ReAct agent structure with tools and prompt template."""
        logger.info("Assembling ReAct Agent...")
        try:
            # ReAct agents work better with a slightly higher temperature for chain of thought
            llm = self._get_llm(temperature=0.2)
            
            tools = create_screening_tools(
                self.vector_store,
                self.scoring_engine,
                self.get_candidate_cache,
                self.get_active_jd
            )
            
            # Self-contained ReAct Prompt Template (safe from network failures or hub deprecations)
            prompt_template = PromptTemplate.from_template(
                "You are a highly capable ATS (Applicant Tracking System) assistant agent. "
                "You help recruitment teams evaluate candidate resumes, search through candidates, "
                "and compare profiles against the active job description.\n\n"
                "You have access to the following tools to complete your task:\n\n"
                "{tools}\n\n"
                "You must strictly format your reasoning using the following keywords:\n"
                "Question: the input question you must answer\n"
                "Thought: you should always think about what to do\n"
                "Action: the action to take, should be one of [{tool_names}]\n"
                "Action Input: the input to the action\n"
                "Observation: the result of the action\n"
                "... (this Thought/Action/Action Input/Observation can repeat multiple times if needed)\n"
                "Thought: I now know the final answer\n"
                "Final Answer: the final answer to the original input question\n\n"
                "Current Active Job Description in the system:\n"
                "\"\"\"\n"
                "{active_jd}\n"
                "\"\"\"\n\n"
                "Chat History:\n"
                "{chat_history}\n\n"
                "Question: {input}\n"
                "Thought: {agent_scratchpad}"
            )
            
            agent = create_react_agent(llm, tools, prompt_template)
            
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=tools,
                verbose=True,
                handle_parsing_errors=True,  # Crucial to recover from ReAct formatting issues
                max_iterations=10
            )
            logger.info("ReAct Agent successfully compiled.")
        except Exception as e:
            raise AgentExecutionError(f"Agent compilation failed: {str(e)}")

    def run_agent(self, user_query: str, chat_history_str: str = "") -> str:
        """Run the compiled ReAct Agent against the user's conversational query.
        
        Args:
            user_query (str): The question to answer.
            chat_history_str (str): Formatted chat history for context.
            
        Returns:
            str: Agent's response.
        """
        # Ensure agent is initialized (lazily, to support API key updates before run)
        if not self.agent_executor:
            self.initialize_agent()
            
        try:
            active_jd = self.get_active_jd() or "No Job Description has been provided yet."
            
            response = self.agent_executor.invoke({
                "input": user_query,
                "chat_history": chat_history_str,
                "active_jd": active_jd
            })
            return response.get("output", "I could not formulate an answer.")
        except Exception as e:
            logger.error(f"Error during ReAct agent run: {str(e)}")
            # Standard user-friendly responses for API failures
            if "api key" in str(e).lower() or "unauthorized" in str(e).lower():
                return (
                    "Error: The LLM API key appears to be invalid or missing. "
                    "Please navigate to the Settings tab, update the key, and try again."
                )
            return f"An execution error occurred in the agent: {str(e)}"
            
    def reset_agent(self):
        """Forces the agent to re-initialize next time it runs (e.g., if API keys or settings change)."""
        self.agent_executor = None
        logger.info("Agent executor reset triggered.")
