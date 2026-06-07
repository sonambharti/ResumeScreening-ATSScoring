import os
import gradio as gr
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Dict, Any, Tuple
from resume_ats_agent.facade import ScreeningSystemFacade
from resume_ats_agent.config.settings import settings
from resume_ats_agent.core.logger import logger

# Initialize the facade system
facade = ScreeningSystemFacade()

def generate_breakdown_chart(skills: float, exp: float, edu: float, cert: float, overall: float) -> plt.Figure:
    """Generate a high-quality horizontal bar chart visualising the candidate's score breakdown."""
    plt.style.use('ggplot')
    fig, ax = plt.subplots(figsize=(6, 3.2), dpi=100)
    
    categories = ['Skills Fit', 'Experience Relevance', 'Education Match', 'Certifications']
    scores = [skills, exp, edu, cert]
    
    # Curated modern colors based on score range
    colors = []
    for s in scores:
        if s >= 80:
            colors.append('#2ec4b6')  # Vibrant Teal
        elif s >= 60:
            colors.append('#ff9f1c')  # Modern Orange
        else:
            colors.append('#e71d36')  # Premium Coral Red
            
    y_pos = np.arange(len(categories))
    
    # Draw horizontal bars
    bars = ax.barh(y_pos, scores, align='center', color=colors, height=0.45)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories, fontsize=10, fontweight='bold', color='#2b2d42')
    ax.invert_yaxis()  # Top-down ordering
    
    ax.set_xlim(0, 100)
    ax.set_xlabel('Score (%)', fontsize=9, fontweight='bold', color='#2b2d42')
    
    # Overlay values on the bars
    for bar in bars:
        width = bar.get_width()
        ax.text(width + 2, bar.get_y() + bar.get_height()/2, f'{width:.0f}%', 
                ha='left', va='center', fontsize=9, fontweight='bold', color='#2b2d42')
                
    # Stylise axis grids and borders
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#cccccc')
    ax.spines['bottom'].set_color('#cccccc')
    ax.grid(axis='x', linestyle='--', alpha=0.5)
    
    fig.patch.set_facecolor('#f8f9fa')
    ax.set_facecolor('#ffffff')
    
    plt.title(f"ATS Score Breakdown (Overall: {overall:.1f}%)", fontsize=11, fontweight='bold', pad=12, color='#1d3557')
    plt.tight_layout()
    return fig

# Local cache for batch reports to allow interactive selection
latest_reports: List[Any] = []

def handle_upload(files: List[Any], jd_text: str) -> str:
    """Callback to process file uploads, setting JD and calling parsing facade."""
    if not files:
        return "No files uploaded."
    
    if not jd_text.strip():
        return "Warning: Resumes uploaded, but Job Description is empty. Please set it before screening."
        
    facade.set_job_description(jd_text)
    
    success_count = 0
    errors = []
    
    for f in files:
        try:
            # Gradio file temp path is f.name
            facade.upload_and_process_resume(f.name)
            success_count += 1
        except Exception as e:
            errors.append(f"{os.path.basename(f.name)}: {str(e)}")
            
    status = f"Successfully parsed and indexed {success_count}/{len(files)} resumes."
    if errors:
        status += "\nErrors:\n" + "\n".join(errors)
    return status

def handle_screening(jd_text: str, w_skills: float, w_exp: float, w_edu: float, w_cert: float) -> Tuple[pd.DataFrame, gr.Dropdown]:
    """Callback to run ATS scoring across all uploaded resumes."""
    global latest_reports
    
    if not jd_text.strip():
        return pd.DataFrame(), gr.Dropdown(choices=[])
        
    facade.set_job_description(jd_text)
    
    weights = {
        "skills": w_skills,
        "experience": w_exp,
        "education": w_edu,
        "certifications": w_cert
    }
    
    try:
        latest_reports = facade.screen_all_candidates(weights)
        
        if not latest_reports:
            return pd.DataFrame([{"Message": "No candidates uploaded yet. Use Tab 1."}]), gr.Dropdown(choices=[])
            
        # Compile data for Gradio Dataframe
        data = []
        choices = []
        for report in latest_reports:
            data.append({
                "Rank": len(data) + 1,
                "Candidate Name": report.candidate_name,
                "ATS Score (%)": report.overall_score,
                "Verdict": report.verdict,
                "Matching Skills": ", ".join(report.skill_matching.matching_skills[:5]) + ("..." if len(report.skill_matching.matching_skills) > 5 else ""),
                "Missing Skills": ", ".join(report.skill_matching.missing_skills[:5]) + ("..." if len(report.skill_matching.missing_skills) > 5 else "")
            })
            choices.append(report.candidate_name)
            
        df = pd.DataFrame(data)
        # Update dropdown choices for profile details view
        return df, gr.Dropdown(choices=choices, value=choices[0] if choices else None, interactive=True)
    except Exception as e:
        logger.error(f"Screening handler error: {str(e)}")
        # Return error df
        return pd.DataFrame([{"Error": str(e)}]), gr.Dropdown(choices=[])

def load_candidate_details(candidate_name: str) -> Tuple[plt.Figure, str]:
    """Load and format the scoring report for the selected candidate."""
    global latest_reports
    if not candidate_name or not latest_reports:
        return plt.figure(), "Select a candidate from the leaderboard."
        
    report = None
    for r in latest_reports:
        if r.candidate_name == candidate_name:
            report = r
            break
            
    if not report:
        return plt.figure(), f"No report found for '{candidate_name}'."
        
    # Generate Matplotlib score breakdown
    fig = generate_breakdown_chart(
        skills=report.breakdown.skills_score,
        exp=report.breakdown.experience_score,
        edu=report.breakdown.education_score,
        cert=report.breakdown.certifications_score,
        overall=report.overall_score
    )
    
    # Format detailed report markdown
    details_md = f"## Evaluation Details for **{report.candidate_name}**\n\n"
    details_md += f"### **Screening Verdict:** `{report.verdict}`\n\n"
    
    details_md += "### **Skill Match Breakdown:**\n"
    details_md += f"- **Matching Skills:** {', '.join(report.skill_matching.matching_skills) if report.skill_matching.matching_skills else '*None matching*'}\n"
    details_md += f"- **Missing Skills:** {', '.join(report.skill_matching.missing_skills) if report.skill_matching.missing_skills else '*None missing*'}\n"
    details_md += f"- **Unrealized Strengths:** {', '.join(report.skill_matching.unrealized_strengths) if report.skill_matching.unrealized_strengths else '*None*'}\n\n"
    
    details_md += f"### **Experience Verdict:**\n{report.experience_verdict}\n\n"
    
    details_md += "### **Actionable Resume Improvements:**\n"
    for feedback in report.improvement_feedback:
        details_md += f"- {feedback}\n"
        
    return fig, details_md

def handle_chat(message: str, history: List[Any]) -> Tuple[str, List[Any]]:
    """Callback for chat queries, forwarding parameters to the ReAct agent facade."""
    if not message.strip():
        return "", history
        
    try:
        bot_response = facade.chat_with_recruiter_agent(message, history)
    except Exception as e:
        logger.error(f"UI Chat Handler caught exception: {str(e)}")
        bot_response = f"⚠️ An error occurred in the agent: {str(e)}"
        
    # Detect the chatbot history format dynamically
    is_messages_format = False
    if history:
        first_msg = history[0]
        if isinstance(first_msg, dict) or (hasattr(first_msg, "role") and hasattr(first_msg, "content")):
            is_messages_format = True
    else:
        # Default to dict/messages format since modern Gradio expects it
        is_messages_format = True
        
    if is_messages_format:
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": bot_response})
    else:
        history.append((message, bot_response))
        
    return "", history

def handle_settings_save(
    provider: str, model: str, openai_key: str, gemini_key: str, groq_key: str,
    embed_provider: str, embed_model: str
) -> str:
    """Save setting values to runtime Singleton configs and reset the agent LLM."""
    settings.default_llm_provider = provider
    settings.default_model_name = model
    settings.openai_api_key = openai_key
    settings.gemini_api_key = gemini_key
    settings.groq_api_key = groq_key
    settings.embedding_provider = embed_provider
    settings.embedding_model_name = embed_model
    
    # Force agent re-initialization on next call
    facade.reset_agent()
    
    logger.info("Application configurations saved.")
    
    # Persist keys and configuration to .env file
    try:
        with open(".env", "w", encoding="utf-8") as f:
            f.write(f"DEFAULT_LLM_PROVIDER={provider}\n")
            f.write(f"DEFAULT_MODEL_NAME={model}\n")
            f.write(f"OPENAI_API_KEY={openai_key}\n")
            f.write(f"GEMINI_API_KEY={gemini_key}\n")
            f.write(f"GROQ_API_KEY={groq_key}\n")
            f.write(f"EMBEDDING_PROVIDER={embed_provider}\n")
            f.write(f"EMBEDDING_MODEL_NAME={embed_model}\n")
        env_msg = " Configurations saved to .env file."
    except Exception as e:
        logger.error(f"Failed to persist configurations to .env file: {str(e)}")
        env_msg = " Warning: Failed to save to .env file."
        
    return f"Settings updated successfully! LLM connection updated.{env_msg}"

def handle_clear() -> Tuple[str, pd.DataFrame, gr.Dropdown, plt.Figure, str, List[Any]]:
    """Clear all databases, indices, and UI tables."""
    facade.clear_database()
    return (
        "Database cleared successfully.",
        pd.DataFrame(),
        gr.Dropdown(choices=[], value=None),
        plt.figure(),
        "Upload resumes and click screening to see details.",
        []
    )

def create_gradio_app() -> gr.Blocks:
    """Constructs the high-fidelity Gradio application interface layout."""
    
    # CSS overrides for premium dark/indigo theme styles
    custom_css = """
    .gradio-container {
        font-family: 'Outfit', 'Inter', -apple-system, sans-serif !important;
        background-color: #fcfcfd !important;
    }
    .main-header {
        background: linear-gradient(135deg, #4f46e5 0%, #1e1b4b 100%);
        padding: 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    }
    .main-header h1 {
        margin: 0;
        font-weight: 800;
        font-size: 2.2rem !important;
        letter-spacing: -0.025em;
    }
    .main-header p {
        margin: 8px 0 0 0;
        opacity: 0.85;
        font-size: 1.1rem;
    }
    .tab-nav {
        border-bottom: 2px solid #e5e7eb !important;
    }
    .action-btn {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
        box-shadow: 0 4px 6px -1px rgba(99, 102, 241, 0.2) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }
    .action-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 12px -1px rgba(99, 102, 241, 0.3) !important;
    }
    .danger-btn {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: white !important;
        font-weight: 600 !important;
    }
    """
    
    with gr.Blocks(theme=gr.themes.Soft(primary_hue="indigo", secondary_hue="slate"), css=custom_css) as app:
        
        # Header Facade
        gr.HTML(
            '<div class="main-header">'
            '  <h1>Resume Screening & ATS Scoring Agent</h1>'
            '  <p>Production-ready LLM-powered Candidate Screening, Semantic RAG Queries, and ReAct Recruiter Agent</p>'
            '</div>'
        )
        
        with gr.Tabs():
            # Tab 1: Database Setup
            with gr.TabItem("1. Upload Job & Resumes", id="upload_tab"):
                with gr.Row():
                    with gr.Column(scale=4):
                        gr.Markdown("### **1. Enter Job Description Requirements**")
                        jd_input = gr.Textbox(
                            label="Job Description (JD)",
                            placeholder="Paste the target job description requirements, skills, and expectations here...",
                            lines=12,
                            max_lines=20
                        )
                    with gr.Column(scale=3):
                        gr.Markdown("### **2. Upload Candidate Resumes**")
                        resume_files = gr.File(
                            label="Resume Documents (.pdf, .docx)",
                            file_count="multiple",
                            file_types=[".pdf", ".docx"]
                        )
                        upload_btn = gr.Button("Upload and Index", elem_classes="action-btn")
                        
                # Upload and operational outputs
                upload_status = gr.Textbox(label="Processing Status", interactive=False)
                clear_db_btn = gr.Button("Clear Database & Local Cache", elem_classes="danger-btn")
                
                upload_btn.click(
                    fn=handle_upload,
                    inputs=[resume_files, jd_input],
                    outputs=[upload_status]
                )
                
            # Tab 2: Screening Dashboard
            with gr.TabItem("2. Screening Dashboard", id="dashboard_tab"):
                gr.Markdown("### **ATS Scoring and Candidate Leaderboard**")
                
                # Dynamic weights configurator
                with gr.Accordion("Adjust Scoring Weights (Category Influence)", open=False):
                    with gr.Row():
                        w_skills = gr.Slider(label="Skills Fit Weight", minimum=0, maximum=1, value=0.40, step=0.05)
                        w_exp = gr.Slider(label="Experience Relevance Weight", minimum=0, maximum=1, value=0.35, step=0.05)
                        w_edu = gr.Slider(label="Education Match Weight", minimum=0, maximum=1, value=0.15, step=0.05)
                        w_cert = gr.Slider(label="Certifications Weight", minimum=0, maximum=1, value=0.10, step=0.05)
                
                screen_btn = gr.Button("Execute ATS Match & Rank", elem_classes="action-btn")
                
                leaderboard = gr.Dataframe(
                    headers=["Rank", "Candidate Name", "ATS Score (%)", "Verdict", "Matching Skills", "Missing Skills"],
                    datatype=["number", "str", "number", "str", "str", "str"],
                    interactive=False
                )
                
                gr.Markdown("---")
                gr.Markdown("### **Detailed Candidate Analysis**")
                
                with gr.Row():
                    with gr.Column(scale=3):
                        candidate_select = gr.Dropdown(
                            label="Select Candidate to Inspect",
                            choices=[],
                            interactive=True
                        )
                        breakdown_plot = gr.Plot(label="Scoring Distribution")
                    with gr.Column(scale=4):
                        candidate_details_md = gr.Markdown(
                            "Upload resumes and click **Execute ATS Match** to see candidate visual breakdowns here."
                        )
                
                screen_btn.click(
                    fn=handle_screening,
                    inputs=[jd_input, w_skills, w_exp, w_edu, w_cert],
                    outputs=[leaderboard, candidate_select]
                )
                
                candidate_select.change(
                    fn=load_candidate_details,
                    inputs=[candidate_select],
                    outputs=[breakdown_plot, candidate_details_md]
                )

            # Tab 3: Interactive Agent
            with gr.TabItem("3. Conversational ReAct Agent", id="agent_tab"):
                gr.Markdown(
                    "### **Interact with the AI Recruiter Agent**\n"
                    "Ask natural language questions about the candidates. The agent utilizes **RAG search** "
                    "across resumes and the **ATS scoring tools** dynamically to answer questions. "
                    "For example: *'Which candidates have Kubernetes experience?'* or *'Tell me why John Doe scored low.'*"
                )
                
                chatbot = gr.Chatbot(label="Agent Chat History", height=450)
                
                with gr.Row():
                    chat_msg = gr.Textbox(
                        label="Ask the agent...",
                        placeholder="e.g., Who is the best candidate for this role and why?",
                        scale=6
                    )
                    chat_submit = gr.Button("Send", scale=1, elem_classes="action-btn")
                    
                clear_chat_btn = gr.Button("Clear Chat History")
                
                # Wire chat actions
                chat_submit.click(
                    fn=handle_chat,
                    inputs=[chat_msg, chatbot],
                    outputs=[chat_msg, chatbot]
                )
                chat_msg.submit(
                    fn=handle_chat,
                    inputs=[chat_msg, chatbot],
                    outputs=[chat_msg, chatbot]
                )
                clear_chat_btn.click(fn=lambda: [], outputs=[chatbot])

            # Tab 4: System Settings
            with gr.TabItem("4. Settings & API Keys", id="settings_tab"):
                gr.Markdown("### **Configure LLM Providers and API Credentials**")
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### **LLM Core Configurations**")
                        llm_provider = gr.Radio(
                            label="LLM Provider",
                            choices=["openai", "gemini", "groq"],
                            value=settings.default_llm_provider
                        )
                        llm_model = gr.Textbox(
                            label="LLM Model Name",
                            value=settings.default_model_name,
                            placeholder="e.g., gpt-4o, gemini-2.5-flash, llama-3.3-70b-versatile"
                        )
                    with gr.Column():
                        gr.Markdown("#### **Embedding Configurations**")
                        embed_provider = gr.Radio(
                            label="Embedding Provider",
                            choices=["openai", "gemini", "huggingface"],
                            value=settings.embedding_provider
                        )
                        embed_model = gr.Textbox(
                            label="Embedding Model Name",
                            value=settings.embedding_model_name,
                            placeholder="e.g., text-embedding-3-small, models/embedding-001"
                        )
                        
                with gr.Row():
                    openai_key_input = gr.Textbox(
                        label="OpenAI API Key",
                        type="password",
                        value=settings.openai_api_key,
                        placeholder="sk-..."
                    )
                    gemini_key_input = gr.Textbox(
                        label="Gemini API Key",
                        type="password",
                        value=settings.gemini_api_key,
                        placeholder="AIzaSy..."
                    )
                    groq_key_input = gr.Textbox(
                        label="Groq API Key",
                        type="password",
                        value=settings.groq_api_key,
                        placeholder="gsk_..."
                    )
                    
                save_settings_btn = gr.Button("Apply and Save Settings", elem_classes="action-btn")
                settings_status = gr.Textbox(label="Status", interactive=False)
                
                save_settings_btn.click(
                    fn=handle_settings_save,
                    inputs=[
                        llm_provider, llm_model, openai_key_input, gemini_key_input, groq_key_input,
                        embed_provider, embed_model
                    ],
                    outputs=[settings_status]
                )

        # Wire clearing action
        clear_db_btn.click(
            fn=handle_clear,
            inputs=[],
            outputs=[
                upload_status, leaderboard, candidate_select, breakdown_plot, candidate_details_md, chatbot
            ]
        )
        
    return app
