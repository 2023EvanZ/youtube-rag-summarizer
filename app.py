import os
import streamlit as st
from dotenv import load_dotenv
import time

from backend.gen_transcript import generate_transcript
from backend.notes_db import get_context_from_chromadb, save_notes, get_transcript_chunks
from backend.main import format_note, extract_video_id
from backend.auth import (
    init_session_state, authenticate_user, create_user, logout,
    require_auth, require_admin, get_all_users, delete_user,
    make_admin, revoke_admin, get_admin_info  # Add this import
)
from backend.metrics import metrics_collector
from langchain.chat_models import init_chat_model

load_dotenv()

# Initialize model
model = init_chat_model(
    "google_genai:gemini-2.5-flash-lite",
    model_kwargs={"temperature": 0.4},
    timeout=60,
)

TRANSCRIPT_FILE = "yt_transcript.txt"

def write_transcript_file_from_db():
    """Optional: if generate_transcript already writes the transcript file"""
    pass

def generate_notes_from_transcript(lines_per_chunk: int = 30) -> str:
    chunks = get_transcript_chunks(lines_per_chunk=lines_per_chunk)
    if not chunks:
        return "No chunks found in transcript."

    notes_blocks = []
    base_prompt = (
        "Summarize the important notes and points of the following text. "
        "Be concise, use bullet points, and structure the notes clearly. "
        "Also present the notes in a language that a fifth grade student can understand. "
        "Use Markdown formatting: **bold** for important terms, *italic* for emphasis. "
        "Do NOT use HTML tags."
    )

    for i, chunk in enumerate(chunks):
        context = get_context_from_chromadb(chunk, n_results=3)
        prompt = (
            f"Use the following context to help summarize the chunk:\n\n{context}\n\n"
            f"{base_prompt}\n\nChunk:\n{chunk}"
        )
        response = model.invoke(prompt)
        raw_note = response.content
        bullets = format_note(raw_note)
        save_notes(raw_note, i)
        joined = "\n".join(f"- {b}" for b in bullets)
        notes_blocks.append(joined)
    
    # Log metrics
    metrics_collector.log_notes(
        st.session_state.user,
        "current_video",
        len(chunks)
    )

    return "\n\n".join(notes_blocks)

def login_page():
    """Login and signup page"""
    st.title("🔐 YouTube RAG Notetaker")
    
    # Center the content
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        # Login Tab
        with tab1:
            st.subheader("Login to Your Account")
            
            login_username = st.text_input("Username", key="login_username")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", use_container_width=True):
                if login_username and login_password:
                    user = authenticate_user(login_username, login_password)
                    if user:
                        st.session_state.authenticated = True
                        st.session_state.user = user["username"]
                        st.session_state.email = user["email"]
                        st.session_state.is_admin = user["is_admin"]
                        
                        metrics_collector.log_request(login_username, "login")
                        
                        st.success(f"Welcome back, {login_username}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")
        
        # Sign Up Tab
        with tab2:
            st.subheader("Create New Account")
            
            signup_username = st.text_input("Username", key="signup_username", 
                                           help="Minimum 3 characters")
            signup_email = st.text_input("Email", key="signup_email")
            signup_password = st.text_input("Password", type="password", key="signup_password",
                                           help="Minimum 6 characters")
            signup_password_confirm = st.text_input("Confirm Password", type="password", 
                                                   key="signup_password_confirm")
            
            if st.button("Create Account", use_container_width=True):
                if not all([signup_username, signup_email, signup_password, signup_password_confirm]):
                    st.warning("⚠️ Please fill in all fields")
                elif signup_password != signup_password_confirm:
                    st.error("❌ Passwords do not match")
                else:
                    success, message = create_user(signup_username, signup_email, signup_password)
                    if success:
                        st.success(f"✅ {message}")
                        st.info("👉 Please login with your new account")
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown("---")
        
        # Get admin info dynamically from .env
        admin_info = get_admin_info()
        st.info(f"""
        **Default Admin Account:**
        - Username: `{admin_info['username']}`
        - Email: `{admin_info['email']}`
        
        ⚠️ Change the admin password after first login!
        """)

def user_page():
    """Regular user page for generating notes"""
    if not require_auth():
        st.warning("⚠️ Please login to access this page")
        return
    
    st.title("📺 YouTube RAG Notetaker")
    
    # Sidebar
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user}**")
        st.caption(f"📧 {st.session_state.email}")
        
        if st.session_state.is_admin:
            st.success("🔑 Admin Account")
        
        if st.button("Logout", use_container_width=True, type="primary"):
            metrics_collector.log_request(st.session_state.user, "logout")
            logout()
        
        st.markdown("---")
        
        # Navigation
        if st.session_state.is_admin:
            st.markdown("### 🎛️ Admin Tools")
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.page = "admin"
                st.rerun()
            if st.button("👥 Manage Users", use_container_width=True):
                st.session_state.page = "users"
                st.rerun()

    st.write(
        "Paste a YouTube URL and this app will:\n"
        "1. Fetch and store the transcript in Chroma,\n"
        "2. Generate bullet-point notes with RAG."
    )

    youtube_url = st.text_input("YouTube URL", key="youtube_url")

    col1, col2 = st.columns(2)
    with col1:
        generate_button = st.button("Generate Transcript + Notes", type="primary")
    with col2:
        clear_button = st.button("Clear Notes/Transcript")

    if clear_button:
        st.info("Clear logic can be added here if desired.")
        metrics_collector.log_request(st.session_state.user, "clear_data")

    if generate_button:
        if not youtube_url.strip():
            st.warning("Please enter a YouTube URL.")
        else:
            try:
                video_id = extract_video_id(youtube_url)
                metrics_collector.log_request(
                    st.session_state.user, 
                    "generate_transcript", 
                    video_id
                )
            except ValueError as e:
                st.error("Could not extract a video ID from that URL.")
                metrics_collector.log_error(
                    st.session_state.user,
                    str(e),
                    "extract_video_id"
                )
            else:
                try:
                    with st.spinner("Generating transcript and storing in Chroma..."):
                        start_time = time.time()
                        generate_transcript(video_id)
                        duration = time.time() - start_time
                        
                        metrics_collector.log_transcript(
                            st.session_state.user,
                            video_id,
                            duration
                        )

                    write_transcript_file_from_db()

                    with st.spinner("Generating notes with RAG..."):
                        notes_text = generate_notes_from_transcript(
                            lines_per_chunk=30,
                        )

                    st.subheader("✅ Generated Notes")
                    st.markdown(notes_text)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Notes",
                        data=notes_text,
                        file_name=f"notes_{video_id}.md",
                        mime="text/markdown"
                    )
                    
                    st.success(f"Notes generated successfully in {duration:.2f}s!")
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    metrics_collector.log_error(
                        st.session_state.user,
                        str(e),
                        "generate_notes"
                    )

def admin_page():
    """Admin dashboard page"""
    if not require_admin():
        st.error("⛔ Admin access required")
        return
    
    st.title("📊 Admin Dashboard")
    
    # Sidebar
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user}** (Admin)")
        
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.page = "user"
            st.rerun()
        
        if st.button("👥 Manage Users", use_container_width=True):
            st.session_state.page = "users"
            st.rerun()
        
        if st.button("Logout", use_container_width=True, type="primary"):
            logout()
        
        st.markdown("---")
        time_range = st.selectbox(
            "Time Range",
            [1, 24, 168],
            format_func=lambda x: f"Last {x} hour{'s' if x > 1 else ''}" if x < 24 else f"Last {x//24} days"
        )
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    
    # Get metrics
    stats = metrics_collector.get_dashboard_stats(hours=time_range)
    
    # Overview metrics
    st.subheader("📈 Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Requests", stats["total_requests"])
    with col2:
        st.metric("Unique Users", stats["unique_users"])
    with col3:
        st.metric("Transcripts", stats["transcripts_generated"])
    with col4:
        st.metric("Notes Generated", stats["notes_generated"])
    
    # Performance metrics
    st.subheader("⚡ Performance")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric(
            "Avg Transcript Time",
            f"{stats['avg_transcript_time']:.2f}s"
        )
    with col2:
        st.metric("Errors", stats["errors"])
    
    # Action breakdown
    st.subheader("📊 Action Breakdown")
    if stats["action_breakdown"]:
        import pandas as pd
        import plotly.express as px
        
        df_actions = pd.DataFrame([
            {"Action": k, "Count": v}
            for k, v in stats["action_breakdown"].items()
        ])
        
        fig = px.bar(df_actions, x="Action", y="Count", 
                     title="Requests by Action Type")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No actions recorded in this time period")
    
    # Top users
    st.subheader("👥 Top Users")
    if stats["top_users"]:
        import pandas as pd
        
        df_users = pd.DataFrame(stats["top_users"])
        st.dataframe(
            df_users,
            column_config={
                "username": "Username",
                "count": st.column_config.NumberColumn("Requests", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No user activity in this time period")
    
    # User activity details
    st.subheader("📋 User Activity Details")
    if stats["user_activity"]:
        import pandas as pd
        
        user_df = pd.DataFrame([
            {
                "Username": username,
                "Total Requests": data["total_requests"],
                "Transcripts": data["transcripts_generated"],
                "Notes": data["notes_generated"],
                "Last Active": data["last_active"]
            }
            for username, data in stats["user_activity"].items()
        ])
        
        st.dataframe(user_df, hide_index=True, use_container_width=True)
    
    # Recent errors
    if stats["recent_errors"]:
        st.subheader("⚠️ Recent Errors")
        for error in stats["recent_errors"]:
            with st.expander(f"{error['timestamp']} - {error['username']}"):
                st.error(error['error'])
                if error.get('context'):
                    st.caption(f"Context: {error['context']}")

def user_management_page():
    """User management page (admin only)"""
    if not require_admin():
        st.error("⛔ Admin access required")
        return
    
    st.title("👥 User Management")
    
    # Sidebar
    with st.sidebar:
        st.write(f"👤 **{st.session_state.user}** (Admin)")
        
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.page = "user"
            st.rerun()
        
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state.page = "admin"
            st.rerun()
        
        if st.button("Logout", use_container_width=True, type="primary"):
            logout()
    
    # Get all users
    users = get_all_users()
    
    st.subheader(f"Total Users: {len(users)}")
    
    # Display users in a table
    import pandas as pd
    
    user_list = []
    for username, data in users.items():
        user_list.append({
            "Username": username,
            "Email": data["email"],
            "Role": "Admin" if data["is_admin"] else "User",
            "Created": data["created_at"][:10] if data["created_at"] else "N/A",
            "Last Login": data["last_login"][:10] if data["last_login"] else "Never"
        })
    
    df = pd.DataFrame(user_list)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    st.subheader("User Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Promote to Admin")
        promote_user = st.selectbox(
            "Select user to promote",
            [u for u in users.keys() if not users[u]["is_admin"]],
            key="promote_user"
        )
        if st.button("Make Admin", use_container_width=True):
            if promote_user:
                success, message = make_admin(promote_user)
                if success:
                    st.success(message)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
    
    with col2:
        st.markdown("#### Revoke Admin")
        demote_user = st.selectbox(
            "Select admin to demote",
            [u for u in users.keys() if users[u]["is_admin"] and u != "admin"],
            key="demote_user"
        )
        if st.button("Revoke Admin", use_container_width=True):
            if demote_user:
                success, message = revoke_admin(demote_user)
                if success:
                    st.success(message)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("---")
    st.subheader("⚠️ Delete User")
    
    delete_username = st.selectbox(
        "Select user to delete",
        [u for u in users.keys() if u != "admin"],
        key="delete_user"
    )
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🗑️ Delete User", use_container_width=True, type="secondary"):
            if delete_username:
                success, message = delete_user(delete_username)
                if success:
                    st.success(message)
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)

def main():
    st.set_page_config(
        page_title="YouTube RAG Notetaker",
        page_icon="📺",
        layout="wide"
    )
    
    # Initialize session state
    init_session_state()
    
    # Initialize page state
    if "page" not in st.session_state:
        st.session_state.page = "user"
    
    # Route to appropriate page
    if not st.session_state.authenticated:
        login_page()
    elif st.session_state.page == "admin":
        admin_page()
    elif st.session_state.page == "users":
        user_management_page()
    else:
        user_page()

if __name__ == "__main__":
    main()