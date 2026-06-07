# Resume Screening and ATS Scoring Agent

This is a modular, production-ready Resume Screening and ATS Scoring Platform built from scratch using LangChain, RAG (Retrieval-Augmented Generation), ReAct agents, and a Gradio UI. 

The application utilizes Python OOP design patterns (Strategy, Factory, Singleton, Facade) to ensure extensibility, maintainability, and clean separation of concerns.

## User Review Required

> [!IMPORTANT]
> **API Keys Configuration**: The application will support both **OpenAI (GPT models)** and **Google (Gemini models)**. Since no API keys were found in the current system environment, the system will support loading keys from a `.env` file or directly inputting them via the Gradio UI Settings panel.
>
> **Vector Database**: We will use `FAISS` (via `faiss-cpu`) as our vector database for RAG. It is lightweight, file-based, runs entirely in-memory, and requires no external database servers, making it ideal for standard installations.

## Open Questions

> [!NOTE]
> There are no blocking open questions at this stage. We have structured the platform to support multiple LLM models (OpenAI and Gemini) and custom weights, providing maximum flexibility to the user.

---

## Proposed Changes

We will create a structured, multi-module Python package under the directory `resume_ats_agent/` alongside the entrypoint scripts.

### 1. Project Configuration & Metadata

#### [NEW] [requirements.txt](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/requirements.txt)
Defines project dependencies.
- `langchain` and `langchain-community`
- `langchain-openai` and `langchain-google-genai`
- `gradio`
- `pypdf`, `pdfplumber`, `python-docx` (resume parsers)
- `faiss-cpu` (vector store)
- `python-dotenv`
- `pydantic`
- `matplotlib` (for scoring visualization charts)

#### [NEW] [.env.example](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/.env.example)
A template for environment variables containing placeholders for LLM API keys and model configurations.

---

### 2. Core Modules & Configuration

#### [NEW] [settings.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/config/settings.py)
Singleton configuration manager handling system configurations, environment variables, API key updates, and default scoring weights.

#### [NEW] [logger.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/core/logger.py)
Standardized logging utility for tracing agent thought processes, RAG retrievals, and scoring operations.

#### [NEW] [exceptions.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/core/exceptions.py)
Custom exception classes (e.g., `ParserError`, `EmbeddingError`, `AgentExecutionError`) to facilitate robust error containment.

#### [NEW] [schemas.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/models/schemas.py)
Pydantic data schemas representing parsed resume structures, ATS evaluation metrics, and matching reports.

---

### 3. Parsing Component (Strategy & Factory Patterns)

#### [NEW] [base.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/parsers/base.py)
Abstract base class `BaseResumeParser` defining the resume parsing interface.

#### [NEW] [pdf_parser.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/parsers/pdf_parser.py)
A concrete parser implementation using `pdfplumber` (primary) and `pypdf` (fallback) to extract textual content from PDF files.

#### [NEW] [docx_parser.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/parsers/docx_parser.py)
A concrete parser implementation using `python-docx` for extracting Word document content.

#### [NEW] [factory.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/parsers/factory.py)
`ResumeParserFactory` class dynamically matching file extensions to their corresponding parser strategy.

---

### 4. RAG & Embedding Component

#### [NEW] [embedding_service.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/rag/embedding_service.py)
Factory providing embedding model instances depending on the active provider (e.g., OpenAIEmbeddings, Gemini/GoogleGenAIEmbeddings, or a fallback lightweight HuggingFace model).

#### [NEW] [vector_store.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/rag/vector_store.py)
Manages resume chunks embedding, indexing in a local FAISS database, loading/saving indexes, and retrieving contextually relevant candidate chunks.

---

### 5. ATS Scoring Engine (Strategy Pattern)

#### [NEW] [scoring.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/engine/scoring.py)
Contains a `ScoringStrategy` base class and concrete scoring algorithms:
- `WeightedScoringStrategy`: Performs keyword match extraction, semantic comparison, experience checks, and education mapping. Calculates scores based on weight settings.
- Uses LLM structure output parsing to fill in ATS scoring attributes.

---

### 6. ReAct Agent & Tools

#### [NEW] [tools.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/agents/tools.py)
Custom LangChain tools giving the agent capabilities to inspect parsed resume sections:
- `AnalyzeResumeTool`: Extract skills, experience history, and credentials.
- `CompareWithJobDescriptionTool`: Perform a detailed gap analysis between a candidate and a specific Job Description.
- `RetrieveSimilarCandidatesTool`: Search the local FAISS RAG index to find candidates matching semantic queries.

#### [NEW] [ats_agent.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/agents/ats_agent.py)
Initializes the ReAct agent executor using LangChain's standard agent capabilities, giving the user a conversational partner that leverages the parsing, scoring, and RAG tools.

---

### 7. Facade & Gradio UI

#### [NEW] [facade.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/facade.py)
`ScreeningSystemFacade` class presenting a unified, high-level API for resume uploading, screening, RAG searches, scoring, and chatting, abstracting lower-level module interactions.

#### [NEW] [app.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/resume_ats_agent/ui/app.py)
Gradio UI containing:
- **Single Profile Analysis**: File upload, JD text block input, beautiful score visualization (pie/bar chart via Matplotlib), keyword alignment checklist, and detailed recommendations.
- **Batch Leaderboard (RAG)**: Multi-file uploader, JD text block input, RAG query input, semantic ranking grid showing name, score, and core match reason.
- **Conversational ReAct Agent**: Chatbox to interact with the LLM-powered screening agent.
- **Settings**: Configuration for LLM providers, model selection, temperature, and scoring weights (e.g., Skills Weight, Experience Weight, Education Weight).

#### [NEW] [main.py](file:///e:/Assignments/Resume%20Screening%20-%20ATS%20Scoring%20Platform/main.py)
The primary entrypoint script to load configuration, initialize the system, and run the Gradio app local server.

---

## Verification Plan

### Automated Tests
We will build a simple validation script to test key modules:
- Run `python -m unittest discover -s tests` if tests are created, or run a custom validation script `verify_system.py` in the scratch directory to verify parsing, database indexing, scoring, and agent initialization.

### Manual Verification
1. Run `python main.py` to launch the local Gradio server.
2. Open the URL (typically `http://127.0.0.1:7860`).
3. Upload a sample PDF/Word resume.
4. Input a standard Job Description (e.g., Software Engineer).
5. Click **Analyze** and verify:
   - Extraction of text is successful.
   - Matplotlib charts render the score breakdown correctly.
   - Recommendation feedback is populated.
6. Upload multiple files, run batch screening, and verify the leaderboard ranks candidates properly.
7. Send questions to the Chatbot (e.g. "Which candidate has the most React experience?") and verify the ReAct agent successfully retrieves information from the RAG tool and formats answers.
