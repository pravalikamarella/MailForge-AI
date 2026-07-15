"""
AI Email Assistant - Streamlit Frontend Application
Features: Compose, Rewrite, Templates Library, Recent History, Exporters.
"""

import streamlit as st
import os
import json
from dotenv import load_dotenv

# Import our modular prompt and utility functions
import prompts
import utils

# Load environment variables
load_dotenv()

# Initialize Database
utils.init_db()

# Page configuration
st.set_page_config(
    page_title="AI Email Assistant - Premium Dashboard",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Premium CSS Injection
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    /* Font style */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Header Gradient styling */
    .app-header {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.5rem;
        margin-bottom: 0.2rem;
    }
    
    .app-subtitle {
        color: #64748b;
        font-size: 1.05rem;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Elegant Container Cards */
    .metric-card {
        background: rgba(99, 102, 241, 0.05);
        border: 1px solid rgba(99, 102, 241, 0.15);
        padding: 0.8rem 1.2rem;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #6366f1;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Custom button enhancements */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }
    
    /* Primary buttons (Generate / Submit) */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
        border: none !important;
        color: white !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    }
    
    /* Secondary buttons (Clear / Reset) */
    div.stButton > button[kind="secondary"]:hover {
        border-color: #6366f1 !important;
        color: #6366f1 !important;
    }
    
    /* Sidebar styling details */
    .sidebar-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #6366f1;
        margin-bottom: 1rem;
    }
    
    /* Writing tips list card */
    .tips-card {
        background-color: rgba(168, 85, 247, 0.05);
        border-left: 4px solid #a855f7;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 1rem;
    }
    
    /* Action items checklist card */
    .actions-card {
        background-color: rgba(16, 185, 129, 0.05);
        border-left: 4px solid #10b981;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 1rem;
    }
    
    /* Footer text */
    .footer-text {
        text-align: center;
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 3rem;
        padding-top: 1.5rem;
        border-top: 1px solid rgba(226, 232, 240, 0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ==========================================
# STATE SYNCHRONIZATION & INITIALIZATION
# ==========================================

# Setup default session state compose keys
if "draft_loaded" not in st.session_state:
    # Attempt to fetch draft autosave from database
    saved = utils.get_draft("active_compose_draft")
    st.session_state.draft_loaded = True
    st.session_state.recipient = saved.get("recipient", "")
    st.session_state.sender = saved.get("sender", "")
    st.session_state.company = saved.get("company", "")
    st.session_state.audience = saved.get("audience", "General Public")
    st.session_state.category = saved.get("category", "Formal")
    st.session_state.subject = saved.get("subject", "")
    st.session_state.details = saved.get("details", "")
    st.session_state.length = saved.get("length", "Medium")
    st.session_state.tone = saved.get("tone", "Professional")
    st.session_state.creativity = float(saved.get("creativity", 0.7))

# Setup session state rewrite keys
if "rewrite_email_input" not in st.session_state:
    st.session_state.rewrite_email_input = ""
if "rewrite_tone" not in st.session_state:
    st.session_state.rewrite_tone = "Professional"
if "rewrite_length" not in st.session_state:
    st.session_state.rewrite_length = "Medium"
if "rewrite_audience" not in st.session_state:
    st.session_state.rewrite_audience = "General Public"
if "rewrite_custom_inst" not in st.session_state:
    st.session_state.rewrite_custom_inst = ""

# Setup session states for active output caches
if "last_generation" not in st.session_state:
    st.session_state.last_generation = None
if "last_rewrite_output" not in st.session_state:
    st.session_state.last_rewrite_output = None

# Navigation switch control
if "nav_page" not in st.session_state:
    st.session_state.nav_page = "📝 Compose"

# API error cache
if "api_error" not in st.session_state:
    st.session_state.api_error = None


# Callback logic to reset compose fields
def reset_compose_fields():
    st.session_state.recipient = ""
    st.session_state.sender = ""
    st.session_state.company = ""
    st.session_state.audience = "General Public"
    st.session_state.category = "Formal"
    st.session_state.subject = ""
    st.session_state.details = ""
    st.session_state.length = "Medium"
    st.session_state.tone = "Professional"
    st.session_state.creativity = 0.7
    st.session_state.last_generation = None
    st.session_state.api_error = None
    utils.save_draft("active_compose_draft", {})
    st.toast("Form reset successfully!")

# Callback logic to clear rewrite inputs
def clear_rewrite_fields():
    st.session_state.rewrite_email_input = ""
    st.session_state.rewrite_custom_inst = ""
    st.session_state.last_rewrite_output = None
    st.toast("Rewrite inputs cleared!")


# ==========================================
# SIDEBAR PANEL - SETTINGS & CONFIG
# ==========================================

with st.sidebar:
    st.markdown('<div class="sidebar-title">⚙️ AI Assistant Panel</div>', unsafe_allow_html=True)
    
    # API Key management (Environment variable first, then text input override)
    env_key = os.getenv("GEMINI_API_KEY", "")
    
    api_key_input = st.text_input(
        "Google Gemini API Key",
        value=st.session_state.get("user_api_key", env_key),
        type="password",
        help="Paste your Google Gemini API key. If left blank, we will try to load it from project environments.",
        placeholder="AIzaSy..."
    )
    # Cache user key in session state
    st.session_state.user_api_key = api_key_input

    mock_mode = st.checkbox(
        "Enable Offline Mock Mode",
        value=st.session_state.get("offline_mock_mode", False),
        help="Test the application interface and exporters using mock AI data without needing a working Gemini API key.",
        key="offline_mock_mode"
    )
    
    # Show key instruction if blank and mock mode is inactive
    if mock_mode:
        st.success("🟢 Offline Mock Mode Active")
    elif not api_key_input:
        st.info("💡 Don't have an API key? You can generate one for free from Google AI Studio.")
        
    model_choice = st.selectbox(
        "AI Generation Model",
        options=["gemini-2.0-flash"],
        index=0,
        help="Choose the Gemini model."
    )
    st.markdown("---")
    st.markdown("**User Personalization**")
    user_sig = st.text_area(
        "Default Email Signature",
        value=st.session_state.get("user_signature", "Best regards,\n[Your Name]"),
        height=80,
        help="Appended to emails if sender details are needed."
    )
    st.session_state.user_signature = user_sig
    
    # Dynamic navigation menu
    st.markdown("---")
    st.markdown("**Navigation Menu**")
    selected_page = st.radio(
        "Go To:",
        ["📝 Compose", "🔄 Refine & Rewrite", "📚 Template Library", "📜 Recent History"],
        key="nav_radio",
        label_visibility="collapsed"
    )
    
    # Sync navigation button and radio clicks
    if selected_page != st.session_state.nav_page:
        st.session_state.nav_page = selected_page
        
    st.markdown("---")
    
    # Reset Config Options
    if st.button("Reset Settings", use_container_width=True):
        st.session_state.user_api_key = ""
        st.session_state.user_signature = "Best regards,\n[Your Name]"
        st.session_state.api_error = None
        st.toast("Settings restored to defaults!")
        st.rerun()
        
    # Autosave indicators
    st.caption("🟢 Autosave is active (SQLite Database)")


# ==========================================
# MAIN APPLICATION INTERFACE
# ==========================================

# Top bar dashboard title
col_title_1, col_title_2 = st.columns([7, 3])
with col_title_1:
    st.markdown('<div class="app-header">Antigravity AI Email Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="app-subtitle">Create, polish, and export production-ready communication drafts in seconds.</div>', unsafe_allow_html=True)

# Keep navigation tab sync active
current_tab = st.session_state.nav_page

# ==========================================
# PAGE 1: COMPOSE EMAIL
# ==========================================
if current_tab == "📝 Compose":
    st.markdown("### 📝 Draft New Email")
    
    # Input Form vs Preview columns
    col_input, col_preview = st.columns([5, 5])
    
    with col_input:
        st.markdown("##### Configuration Fields")
        
        # Recipients details in columns
        col_rec_1, col_rec_2 = st.columns(2)
        with col_rec_1:
            recipient_val = st.text_input("Recipient Name", value=st.session_state.recipient, placeholder="Jane Doe", key="recipient_input")
            # Update session state immediately
            st.session_state.recipient = recipient_val
        with col_rec_2:
            sender_val = st.text_input("Sender Name", value=st.session_state.sender, placeholder="John Smith", key="sender_input")
            st.session_state.sender = sender_val
            
        col_rec_3, col_rec_4 = st.columns(2)
        with col_rec_3:
            company_val = st.text_input("Company Name (Optional)", value=st.session_state.company, placeholder="Acme Inc.", key="company_input")
            st.session_state.company = company_val
        with col_rec_4:
            audience_val = st.selectbox(
                "Target Audience",
                options=["General Public", "Executives/Leadership", "Technical Team", "Clients/Customers", "Internal Staff"],
                index=["General Public", "Executives/Leadership", "Technical Team", "Clients/Customers", "Internal Staff"].index(st.session_state.audience),
                key="audience_input"
            )
            st.session_state.audience = audience_val
            
        # Email settings
        col_sett_1, col_sett_2 = st.columns(2)
        with col_sett_1:
            category_val = st.selectbox(
                "Email Category",
                options=[
                    "Formal", "Informal", "Leave Request", "Job Application", "Complaint", 
                    "Customer Support", "Follow-up", "Meeting Request", "Sales Pitch", 
                    "Thank You", "Apology", "Invitation"
                ],
                index=[
                    "Formal", "Informal", "Leave Request", "Job Application", "Complaint", 
                    "Customer Support", "Follow-up", "Meeting Request", "Sales Pitch", 
                    "Thank You", "Apology", "Invitation"
                ].index(st.session_state.category),
                key="category_input"
            )
            st.session_state.category = category_val
        with col_sett_2:
            tone_val = st.selectbox(
                "Email Tone",
                options=["Professional", "Friendly", "Confident", "Persuasive", "Polite", "Empathetic", "Urgent"],
                index=["Professional", "Friendly", "Confident", "Persuasive", "Polite", "Empathetic", "Urgent"].index(st.session_state.tone),
                key="tone_input"
            )
            st.session_state.tone = tone_val
            
        # Length & Creativity Slider
        col_sett_3, col_sett_4 = st.columns(2)
        with col_sett_3:
            length_val = st.selectbox(
                "Desired Length",
                options=["Short", "Medium", "Detailed"],
                index=["Short", "Medium", "Detailed"].index(st.session_state.length),
                key="length_input"
            )
            st.session_state.length = length_val
        with col_sett_4:
            creativity_val = st.slider(
                "Creativity / Temperature",
                min_value=0.0,
                max_value=1.5,
                value=st.session_state.creativity,
                step=0.1,
                help="Higher values yield more creative outputs. Low values are direct.",
                key="creativity_input"
            )
            st.session_state.creativity = creativity_val

        # Core context
        subject_val = st.text_input(
            "Subject Line Idea / Core Topic",
            value=st.session_state.subject,
            placeholder="E.g., Request for annual vacation next month",
            key="subject_input"
        )
        st.session_state.subject = subject_val
        
        details_val = st.text_area(
            "Email Details / Key Points to Include",
            value=st.session_state.details,
            placeholder="Add specific context here. What are the key details of the message?",
            height=140,
            key="details_input"
        )
        st.session_state.details = details_val
        
        # Real-time writing counts
        stats = utils.get_text_stats(details_val)
        col_stat_1, col_stat_2, col_stat_3 = st.columns(3)
        with col_stat_1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{stats["words"]}</div><div class="metric-label">Words Input</div></div>', unsafe_allow_html=True)
        with col_stat_2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{stats["chars"]}</div><div class="metric-label">Characters</div></div>', unsafe_allow_html=True)
        with col_stat_3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{stats["reading_time"]}</div><div class="metric-label">Est. Read Time</div></div>', unsafe_allow_html=True)
            
        st.write("")
        
        # Smart Local Client-side validation Warnings
        missing_fields = []
        if not subject_val:
            missing_fields.append("Subject Idea")
        if not details_val:
            missing_fields.append("Email Details")
        if not recipient_val:
            missing_fields.append("Recipient Name")
        if not sender_val:
            missing_fields.append("Sender Name")
            
        if missing_fields:
            st.warning(f"⚠️ Recommendation: Fill out {', '.join(missing_fields)} for the best generation results.")
            
        # Generation control buttons
        col_btn_1, col_btn_2 = st.columns([1, 1])
        with col_btn_1:
            generate_click = st.button("🚀 Generate Email", type="primary", use_container_width=True)
        with col_btn_2:
            st.button("🧹 Clear Form & Reset", type="secondary", use_container_width=True, on_click=reset_compose_fields)
            
        # Call API on click
        if generate_click:
            # Enforce validation
            if not details_val and not subject_val:
                st.error("❌ Submission Blocked: Please fill in either the Subject Line or the Email Details to generate an email.")
            elif not api_key_input and not mock_mode:
                st.error("❌ API Key Missing: Please provide a Gemini API Key in the sidebar configuration.")
            else:
                with st.spinner("AI email assistant is drafting your communication..."):
                    # Build full prompt
                    full_prompt = prompts.GENERATE_EMAIL_PROMPT.format(
                        subject_input=subject_val,
                        details_input=details_val,
                        category=category_val,
                        recipient_name=recipient_val,
                        sender_name=sender_val,
                        company_name=company_val if company_val else "N/A",
                        target_audience=audience_val,
                        length=length_val,
                        tone=tone_val
                    )
                    
                    try:
                        st.session_state.api_error = None
                        # Call Gemini Client
                        response_data = utils.call_gemini(
                            api_key=api_key_input,
                            model_name=model_choice,
                            system_instruction=prompts.SYSTEM_INSTRUCTION,
                            prompt=full_prompt,
                            creativity=creativity_val,
                            mock_mode=mock_mode
                        )
                        
                        # Cache output
                        st.session_state.last_generation = response_data
                        
                        # Save successful generation to history
                        utils.save_history(
                            email_type="Generation",
                            subject=response_data.get("subject", ""),
                            body=response_data.get("body", ""),
                            recipient=recipient_val,
                            sender=sender_val,
                            category=category_val,
                            tone=tone_val,
                            length=length_val,
                            action_items=response_data.get("action_items", []),
                            writing_tips=response_data.get("writing_tips", [])
                        )
                        
                        st.success("🎉 Email draft generated successfully!")
                    except Exception as e:
                        st.session_state.api_error = str(e)
                        st.error(f"❌ Generation Failed: {str(e)}")
                        
        # Autosave draft state to database triggers on reruns
        draft_state = {
            "recipient": recipient_val,
            "sender": sender_val,
            "company": company_val,
            "audience": audience_val,
            "category": category_val,
            "subject": subject_val,
            "details": details_val,
            "length": length_val,
            "tone": tone_val,
            "creativity": creativity_val
        }
        utils.save_draft("active_compose_draft", draft_state)

    # RIGHT COLUMN: PREVIEW PANEL
    with col_preview:
        st.markdown("##### ✉️ Instant Preview Panel")
        
        output_data = st.session_state.last_generation
        
        if output_data:
            # Missing details flags generated by LLM
            warnings = output_data.get("missing_info_warnings", [])
            if warnings and warnings[0] != "" and len(warnings) > 0 and warnings != [""]:
                for warn in warnings:
                    if warn.strip():
                        st.warning(f"💡 LLM Notice: {warn}")
            
            # Interactive tab layout for Primary vs Alternatives
            output_tabs = st.tabs(["⭐ Primary Version", "🔄 Alt Version 1", "🔄 Alt Version 2", "🔄 Alt Version 3"])
            
            # --- PRIMARY VERSION TAB ---
            with output_tabs[0]:
                primary_subject = output_data.get("subject", "")
                primary_body = output_data.get("body", "")
                
                # Render inputs inside layout
                st.text_input("Generated Subject", value=primary_subject, key="primary_subj_view")
                st.text_area("Generated Email Body", value=primary_body, height=320, key="primary_body_view")
                
                # Fetch counts
                out_stats = utils.get_text_stats(primary_body)
                st.caption(f"Words: {out_stats['words']} | Characters: {out_stats['chars']} | Reading Time: {out_stats['reading_time']}")
                
                # Exporters Layout
                col_exp_1, col_exp_2 = st.columns(2)
                with col_exp_1:
                    # Download TXT
                    txt_bytes = utils.generate_txt(
                        subject=primary_subject,
                        body=primary_body,
                        sender=sender_val,
                        recipient=recipient_val,
                        category=category_val,
                        tone=tone_val
                    )
                    st.download_button(
                        label="📥 Download TXT Draft",
                        data=txt_bytes,
                        file_name=f"email_{category_val.lower()}_draft.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                with col_exp_2:
                    # Download PDF
                    try:
                        pdf_bytes = utils.generate_pdf(
                            subject=primary_subject,
                            body=primary_body,
                            sender=sender_val,
                            recipient=recipient_val,
                            category=category_val,
                            tone=tone_val
                        )
                        st.download_button(
                            label="📄 Download PDF Document",
                            data=pdf_bytes,
                            file_name=f"email_{category_val.lower()}_draft.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as pe:
                        st.button("PDF Generation Error", disabled=True, use_container_width=True)
                        st.caption(f"Could not build PDF: {str(pe)}")
                        
            # --- ALTERNATIVE TABS ---
            alts = output_data.get("alternatives", [])
            for idx in range(3):
                with output_tabs[idx + 1]:
                    if len(alts) > idx:
                        alt_subject = alts[idx].get("subject", "")
                        alt_body = alts[idx].get("body", "")
                        
                        st.text_input(f"Alt {idx+1} Subject", value=alt_subject, key=f"alt_subj_view_{idx}")
                        st.text_area(f"Alt {idx+1} Body", value=alt_body, height=280, key=f"alt_body_view_{idx}")
                        
                        # Action to promote this to primary
                        def make_primary_callback(subj=alt_subject, bdy=alt_body):
                            st.session_state.last_generation["subject"] = subj
                            st.session_state.last_generation["body"] = bdy
                            st.toast("Alternative promoted to Primary Draft!")
                            
                        st.button(
                            "⭐ Promote to Primary Draft",
                            key=f"promote_btn_{idx}",
                            on_click=make_primary_callback,
                            use_container_width=True
                        )
                    else:
                        st.info("No alternative variant generated.")
                        
            # Show Action items and tips below
            col_act, col_tips = st.columns(2)
            with col_act:
                st.markdown('<div class="actions-card">', unsafe_allow_html=True)
                st.markdown("**✅ Key Action Items**")
                for action in output_data.get("action_items", []):
                    st.markdown(f"- {action}")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col_tips:
                st.markdown('<div class="tips-card">', unsafe_allow_html=True)
                st.markdown("**💡 Writing Tips & Best Practices**")
                for tip in output_data.get("writing_tips", []):
                    st.markdown(f"- {tip}")
                st.markdown('</div>', unsafe_allow_html=True)
                
        else:
            st.info("👋 Enter email criteria on the left and click 'Generate Email' to view the draft output here.")
            
            # Show a helpful guide card on startup
            st.markdown(
                """
                <div style="border-radius: 12px; background: rgba(99, 102, 241, 0.03); border: 1px dashed rgba(99, 102, 241, 0.2); padding: 1.5rem; margin-top: 1rem;">
                    <h5>💡 Quick Tips for High-Quality Emails:</h5>
                    <ul style="margin-bottom: 0;">
                        <li><strong>Be specific:</strong> Include critical information (dates, times, locations) in the details box.</li>
                        <li><strong>Select appropriate tone:</strong> Use 'Urgent' or 'Empathetic' to adjust communication context.</li>
                        <li><strong>Autosave:</strong> Refreshing the browser will restore your inputs automatically from our local database draft.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )


# ==========================================
# PAGE 2: REFINE & REWRITE
# ==========================================
elif current_tab == "🔄 Refine & Rewrite":
    st.markdown("### 🔄 Rewrite & Polish Existing Emails")
    st.markdown("Paste an email draft below to adjust its tone, length, fix grammatical errors, or extract action tasks.")
    
    col_rw_in, col_rw_out = st.columns([5, 5])
    
    with col_rw_in:
        st.markdown("##### 📥 Input Existing Draft")
        original_draft = st.text_area(
            "Paste Email Body",
            value=st.session_state.rewrite_email_input,
            placeholder="Paste your rough email draft here...",
            height=220,
            key="rewrite_input_area"
        )
        st.session_state.rewrite_email_input = original_draft
        
        # Word counts
        rw_stats = utils.get_text_stats(original_draft)
        st.caption(f"Words: {rw_stats['words']} | Characters: {rw_stats['chars']}")
        
        # Settings columns
        col_rws_1, col_rws_2 = st.columns(2)
        with col_rws_1:
            rw_tone = st.selectbox(
                "Target Tone",
                options=["Professional", "Friendly", "Confident", "Persuasive", "Polite", "Empathetic", "Urgent"],
                index=["Professional", "Friendly", "Confident", "Persuasive", "Polite", "Empathetic", "Urgent"].index(st.session_state.rewrite_tone),
                key="rw_tone_sel"
            )
            st.session_state.rewrite_tone = rw_tone
        with col_rws_2:
            rw_length = st.selectbox(
                "Target Length",
                options=["Short", "Medium", "Detailed"],
                index=["Short", "Medium", "Detailed"].index(st.session_state.rewrite_length),
                key="rw_length_sel"
            )
            st.session_state.rewrite_length = rw_length
            
        rw_audience = st.selectbox(
            "Target Audience Context",
            options=["General Public", "Executives/Leadership", "Technical Team", "Clients/Customers", "Internal Staff"],
            index=["General Public", "Executives/Leadership", "Technical Team", "Clients/Customers", "Internal Staff"].index(st.session_state.rewrite_audience),
            key="rw_audience_sel"
        )
        st.session_state.rewrite_audience = rw_audience
        
        rw_inst = st.text_input(
            "Custom Refinement/Rewrite Request (Optional)",
            value=st.session_state.rewrite_custom_inst,
            placeholder="E.g., Make it sound more enthusiastic; Add details about the invoice.",
            key="rw_inst_input"
        )
        st.session_state.rewrite_custom_inst = rw_inst
        
        # Action Buttons Grid
        st.markdown("##### ⚡ Quick Transformation Operations")
        
        col_g_1, col_g_2 = st.columns(2)
        with col_g_1:
            submit_rewrite = st.button("🪄 Custom Rewrite & Polish", type="primary", use_container_width=True)
            grammar_polish = st.button("✨ Improve Grammar & Style", use_container_width=True)
        with col_g_2:
            tone_change = st.button("🎭 Shift Tone Instantly", use_container_width=True)
            clear_rw = st.button("🧹 Clear Form Fields", type="secondary", use_container_width=True, on_click=clear_rewrite_fields)
            
        # Execute Rewrite logic
        trigger_rewrite = False
        custom_action_prompt = ""
        
        if submit_rewrite:
            if not original_draft:
                st.error("Please paste an email body to rewrite.")
            elif not api_key_input and not mock_mode:
                st.error("Google Gemini API Key is missing. Add it in the sidebar.")
            else:
                trigger_rewrite = True
                custom_action_prompt = prompts.REWRITE_EMAIL_PROMPT.format(
                    original_email=original_draft,
                    tone=rw_tone,
                    length=rw_length,
                    target_audience=rw_audience,
                    refinement_instructions=rw_inst if rw_inst else "Optimize and refine details."
                )
                
        elif grammar_polish:
            if not original_draft:
                st.error("Please paste an email body to rewrite.")
            elif not api_key_input and not mock_mode:
                st.error("Google Gemini API Key is missing.")
            else:
                trigger_rewrite = True
                custom_action_prompt = prompts.REWRITE_EMAIL_PROMPT.format(
                    original_email=original_draft,
                    tone="Professional",
                    length=rw_length,
                    target_audience=rw_audience,
                    refinement_instructions="Focus completely on correcting grammar, vocabulary, sentence structures, flow, and making it sound highly polished and professional."
                )
                
        elif tone_change:
            if not original_draft:
                st.error("Please paste an email body to rewrite.")
            elif not api_key_input and not mock_mode:
                st.error("Google Gemini API Key is missing.")
            else:
                trigger_rewrite = True
                custom_action_prompt = prompts.REWRITE_EMAIL_PROMPT.format(
                    original_email=original_draft,
                    tone=rw_tone,
                    length=rw_length,
                    target_audience=rw_audience,
                    refinement_instructions=f"Shift the tone to {rw_tone} immediately. Do not alter core details, but change phrasing to embody {rw_tone}."
                )
                
        if trigger_rewrite:
            with st.spinner("AI email assistant is adjusting draft..."):
                try:
                    st.session_state.api_error = None
                    response_data = utils.call_gemini(
                        api_key=api_key_input,
                        model_name=model_choice,
                        system_instruction=prompts.SYSTEM_INSTRUCTION,
                        prompt=custom_action_prompt,
                        creativity=0.6,
                        mock_mode=mock_mode
                    )
                    
                    st.session_state.last_rewrite_output = response_data
                    
                    # Save successful operation to database
                    utils.save_history(
                        email_type="Rewrite",
                        subject=response_data.get("subject", "Rewritten Email"),
                        body=response_data.get("body", ""),
                        recipient="N/A",
                        sender="N/A",
                        category="Rewrite",
                        tone=rw_tone,
                        length=rw_length,
                        action_items=response_data.get("action_items", []),
                        writing_tips=response_data.get("writing_tips", [])
                    )
                    
                    st.success("🎉 Email rewrite complete!")
                except Exception as e:
                    st.session_state.api_error = str(e)
                    st.error(f"❌ Rewrite Failed: {str(e)}")

    with col_rw_out:
        st.markdown("##### ✉️ Refined Output Preview")
        
        rw_output = st.session_state.last_rewrite_output
        
        if rw_output:
            rw_subj = rw_output.get("subject", "Rewritten Email")
            rw_body = rw_output.get("body", "")
            
            st.text_input("Refined Subject", value=rw_subj, key="rw_subj_out_view")
            st.text_area("Refined Email Body", value=rw_body, height=320, key="rw_body_out_view")
            
            out_rw_stats = utils.get_text_stats(rw_body)
            st.caption(f"Words: {out_rw_stats['words']} | Characters: {out_rw_stats['chars']} | Reading Time: {out_rw_stats['reading_time']}")
            
            # Export Columns
            col_rwe_1, col_rwe_2 = st.columns(2)
            with col_rwe_1:
                # TXT
                txt_bytes = utils.generate_txt(
                    subject=rw_subj,
                    body=rw_body,
                    sender=st.session_state.sender,
                    recipient=st.session_state.recipient,
                    category="Rewrite",
                    tone=rw_tone
                )
                st.download_button(
                    label="📥 Download TXT Draft",
                    data=txt_bytes,
                    file_name="email_rewrite_draft.txt",
                    mime="text/plain",
                    use_container_width=True,
                    key="rw_txt_btn"
                )
            with col_rwe_2:
                # PDF
                try:
                    pdf_bytes = utils.generate_pdf(
                        subject=rw_subj,
                        body=rw_body,
                        sender=st.session_state.sender,
                        recipient=st.session_state.recipient,
                        category="Rewrite",
                        tone=rw_tone
                    )
                    st.download_button(
                        label="📄 Download PDF Document",
                        data=pdf_bytes,
                        file_name="email_rewrite_draft.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key="rw_pdf_btn"
                    )
                except Exception as pe:
                    st.button("PDF Generation Error", disabled=True, use_container_width=True, key="rw_pdf_err")
                    st.caption(f"Could not build PDF: {str(pe)}")
            
            # Show action items and tips
            col_act, col_tips = st.columns(2)
            with col_act:
                st.markdown('<div class="actions-card">', unsafe_allow_html=True)
                st.markdown("**✅ Tasks & Actions**")
                for action in rw_output.get("action_items", []):
                    st.markdown(f"- {action}")
                st.markdown('</div>', unsafe_allow_html=True)
                
            with col_tips:
                st.markdown('<div class="tips-card">', unsafe_allow_html=True)
                st.markdown("**💡 Changes Summary**")
                for tip in rw_output.get("writing_tips", []):
                    st.markdown(f"- {tip}")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Paste copy into the left container and trigger a quick action to view results here.")


# ==========================================
# PAGE 3: TEMPLATES LIBRARY
# ==========================================
elif current_tab == "📚 Template Library":
    st.markdown("### 📚 AI Presets & Email Templates Library")
    st.markdown("Click any preset template to pre-fill the Compose form fields instantly.")
    
    # Grid of standard templates
    templates_list = [
        {
            "name": "Formal resignation letter",
            "emoji": "👋",
            "subject": "Resignation - [My Name]",
            "category": "Formal",
            "tone": "Polite",
            "length": "Medium",
            "audience": "Executives/Leadership",
            "details": "I am writing to formally resign from my position as Software Engineer. My last day will be July 30, 2026. I want to thank the entire company for the support and career opportunities. I will assist in training my replacement during my two-week notice period."
        },
        {
            "name": "Cold sales outreach email",
            "emoji": "📈",
            "subject": "Automating your workflow - Antigravity Solutions",
            "category": "Sales Pitch",
            "tone": "Persuasive",
            "length": "Short",
            "audience": "Clients/Customers",
            "details": "Introducing our cloud tool which automates receipt filing using smart OCR. We save small business owners an average of 12 hours a week. I'd love to schedule a brief 10-minute demo this coming Thursday or Friday."
        },
        {
            "name": "Personalized sick leave notice",
            "emoji": "🤒",
            "subject": "Sick Leave Request - [My Name]",
            "category": "Leave Request",
            "tone": "Polite",
            "length": "Short",
            "audience": "Internal Staff",
            "details": "I woke up feeling unwell with a high fever and headache. I won't be able to work today. I will check urgent Slack messages occasionally but will primarily be resting. I have updated my team on the daily tasks."
        },
        {
            "name": "Follow-up on job application",
            "emoji": "💼",
            "subject": "Follow-up: Full-stack Developer Role",
            "category": "Follow-up",
            "tone": "Confident",
            "length": "Short",
            "audience": "Executives/Leadership",
            "details": "I submitted my application for the Full-stack Developer position two weeks ago. I am writing to check in on the status of my application. I am very interested in the role and believe my skills align perfectly."
        },
        {
            "name": "Apology for service disruption",
            "emoji": "⚠️",
            "subject": "Apology: Database Outage Incident",
            "category": "Apology",
            "tone": "Empathetic",
            "length": "Medium",
            "audience": "Clients/Customers",
            "details": "Apologizing for the database connection downtime yesterday, which lasted 3 hours. Our engineering team has resolved the scaling issue. We are issuing a 15% credit to all client accounts for this month."
        },
        {
            "name": "Meeting request with team lead",
            "emoji": "🗓️",
            "subject": "Q3 Planning Sync Request",
            "category": "Meeting Request",
            "tone": "Professional",
            "length": "Short",
            "audience": "Technical Team",
            "details": "Requesting a 30-minute sync session to align on our developer sprint deliverables and deadlines for Q3. Please let me know your availability for Tuesday morning."
        }
    ]
    
    # Display in a 2x3 grid
    row1 = st.columns(3)
    row2 = st.columns(3)
    
    for idx, temp in enumerate(templates_list):
        grid_col = row1[idx] if idx < 3 else row2[idx - 3]
        
        with grid_col:
            st.markdown(
                f"""
                <div style="border: 1px solid rgba(99, 102, 241, 0.2); border-radius: 12px; padding: 1.2rem; background: rgba(99, 102, 241, 0.02); height: 260px; display: flex; flex-direction: column; justify-content: space-between; margin-bottom: 1.2rem;">
                    <div>
                        <h4 style="margin: 0 0 0.5rem 0;">{temp['emoji']} {temp['name']}</h4>
                        <p style="font-size: 0.85rem; color: #64748b; line-height: 1.4; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical;">
                            {temp['details']}
                        </p>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Button callback to load template parameters
            def make_loader(t=temp):
                return lambda: load_template_data(t)
                
            def load_template_data(t):
                st.session_state.recipient = "[Name]"
                st.session_state.sender = "[Your Name]"
                st.session_state.company = "[Company]"
                st.session_state.audience = t["audience"]
                st.session_state.category = t["category"]
                st.session_state.subject = t["subject"]
                st.session_state.details = t["details"]
                st.session_state.length = t["length"]
                st.session_state.tone = t["tone"]
                st.session_state.last_generation = None
                st.session_state.api_error = None
                
                # Update draft immediately
                draft_state = {
                    "recipient": "[Name]",
                    "sender": "[Your Name]",
                    "company": "[Company]",
                    "audience": t["audience"],
                    "category": t["category"],
                    "subject": t["subject"],
                    "details": t["details"],
                    "length": t["length"],
                    "tone": t["tone"],
                    "creativity": 0.7
                }
                utils.save_draft("active_compose_draft", draft_state)
                
                st.session_state.nav_page = "📝 Compose"
                # Set radio session state key
                st.session_state.nav_radio = "📝 Compose"
                st.toast(f"✅ Prefilled fields for: '{t['name']}'! Switch to Compose tab.")
                
            st.button(f"Load '{temp['name']}' Preset", key=f"temp_load_btn_{idx}", on_click=make_loader(temp), use_container_width=True)


# ==========================================
# PAGE 4: HISTORY VIEW
# ==========================================
elif current_tab == "📜 Recent History":
    st.markdown("### 📜 Generation & Refine History logs")
    st.markdown("Inspect, restore, or export previously generated email assistant records.")
    
    # Retrieve logs
    history_items = utils.get_history(limit=30)
    
    if not history_items:
        st.info("No logs saved yet. Emails generated or rewritten will show up here.")
    else:
        # Header control actions
        col_clear_1, col_clear_2 = st.columns([8, 2])
        with col_clear_2:
            if st.button("🧹 Wipe History Log", type="secondary", use_container_width=True):
                utils.clear_history()
                st.toast("Database logs purged!")
                st.rerun()
                
        # Loop and render logs in styled accordions
        for idx, item in enumerate(history_items):
            with st.expander(f"✉️ {item['timestamp']} - [{item['email_type'].upper()}] Subject: {item['subject'][:45]}..."):
                st.write("")
                col_hmeta_1, col_hmeta_2, col_hmeta_3, col_hmeta_4 = st.columns(4)
                with col_hmeta_1:
                    st.write(f"**Recipient:** {item['recipient']}")
                with col_hmeta_2:
                    st.write(f"**Sender:** {item['sender']}")
                with col_hmeta_3:
                    st.write(f"**Category:** {item['category']}")
                with col_hmeta_4:
                    st.write(f"**Tone:** {item['tone']} | **Length:** {item['length']}")
                    
                st.text_area("Email Draft Text", value=item["body"], height=200, key=f"hist_txt_area_{idx}", disabled=True)
                
                # Restore functions
                col_hbtn_1, col_hbtn_2, col_hbtn_3, col_hbtn_4 = st.columns(4)
                
                with col_hbtn_1:
                    def make_restore_compose(it=item):
                        return lambda: restore_to_compose(it)
                        
                    def restore_to_compose(it):
                        st.session_state.recipient = it["recipient"]
                        st.session_state.sender = it["sender"]
                        st.session_state.company = ""
                        st.session_state.category = it["category"] if it["category"] in [
                            "Formal", "Informal", "Leave Request", "Job Application", "Complaint", 
                            "Customer Support", "Follow-up", "Meeting Request", "Sales Pitch", 
                            "Thank You", "Apology", "Invitation"
                        ] else "Formal"
                        st.session_state.subject = it["subject"]
                        st.session_state.details = it["body"]
                        st.session_state.length = it["length"] if it["length"] in ["Short", "Medium", "Detailed"] else "Medium"
                        st.session_state.tone = it["tone"] if it["tone"] in ["Professional", "Friendly", "Confident", "Persuasive", "Polite", "Empathetic", "Urgent"] else "Professional"
                        
                        # Set compose cache
                        st.session_state.last_generation = {
                            "subject": it["subject"],
                            "body": it["body"],
                            "alternatives": [],
                            "action_items": it["action_items"],
                            "writing_tips": it["writing_tips"]
                        }
                        
                        st.session_state.nav_page = "📝 Compose"
                        st.session_state.nav_radio = "📝 Compose"
                        st.toast("Restored draft fields to Compose tab!")
                        
                    st.button("📝 Restore to Compose", key=f"hist_rest_comp_{idx}", on_click=make_restore_compose(item), use_container_width=True)
                    
                with col_hbtn_2:
                    def make_restore_rewrite(it=item):
                        return lambda: restore_to_rewrite(it)
                        
                    def restore_to_rewrite(it):
                        st.session_state.rewrite_email_input = it["body"]
                        st.session_state.rewrite_tone = it["tone"] if it["tone"] in ["Professional", "Friendly", "Confident", "Persuasive", "Polite", "Empathetic", "Urgent"] else "Professional"
                        st.session_state.rewrite_length = it["length"] if it["length"] in ["Short", "Medium", "Detailed"] else "Medium"
                        st.session_state.last_rewrite_output = {
                            "subject": it["subject"],
                            "body": it["body"],
                            "action_items": it["action_items"],
                            "writing_tips": it["writing_tips"]
                        }
                        
                        st.session_state.nav_page = "🔄 Refine & Rewrite"
                        st.session_state.nav_radio = "🔄 Refine & Rewrite"
                        st.toast("Restored draft to Refine & Rewrite tab!")
                        
                    st.button("🔄 Restore to Rewrite", key=f"hist_rest_rw_{idx}", on_click=make_restore_rewrite(item), use_container_width=True)
                    
                with col_hbtn_3:
                    # PDF Export from logs
                    try:
                        pdf_bytes = utils.generate_pdf(
                            subject=item["subject"],
                            body=item["body"],
                            sender=item["sender"],
                            recipient=item["recipient"],
                            category=item["category"],
                            tone=item["tone"]
                        )
                        st.download_button(
                            label="📄 Export PDF Document",
                            data=pdf_bytes,
                            file_name=f"history_email_{item['id']}.pdf",
                            mime="application/pdf",
                            key=f"hist_pdf_dl_{idx}",
                            use_container_width=True
                        )
                    except Exception:
                        st.button("PDF Build Error", disabled=True, key=f"hist_pdf_err_{idx}", use_container_width=True)
                        
                with col_hbtn_4:
                    def make_delete_action(iid=item["id"]):
                        return lambda: delete_log(iid)
                        
                    def delete_log(iid):
                        utils.delete_history_item(iid)
                        st.toast("History log entry deleted.")
                        
                    st.button("❌ Delete Log Entry", key=f"hist_del_btn_{idx}", on_click=make_delete_action(item["id"]), use_container_width=True)


# ==========================================
# FOOTER CREDITS
# ==========================================
st.markdown(
    """
    <div class="footer-text">
        Antigravity AI Email Assistant | Powered by Google Gemini Generative Models | Built with Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
