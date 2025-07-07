"""
StudyMateAI Dashboard - Streamlit Web Interface
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import os
from datetime import datetime

# Import our modules
import config
import utils
from utils import logger

st.set_page_config(
    page_title="StudyMateAI Dashboard",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_assignment_stats():
    """Load assignment statistics"""
    assignment_files = list(config.ASSIGNMENT_DIR.glob("*.txt"))
    answer_files = list(config.ASSIGNMENT_ANSWERS_DIR.glob("*.txt"))
    
    total_assignments = len(assignment_files)
    completed_assignments = len(answer_files)
    completion_rate = (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
    
    return {
        "total": total_assignments,
        "completed": completed_assignments,
        "completion_rate": completion_rate,
        "assignment_files": assignment_files,
        "answer_files": answer_files
    }

def main():
    st.title("📚 StudyMateAI Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page",
        ["Overview", "Assignments", "Q&A", "Document Manager", "Download Manager", "Settings"]
    )
    
    if page == "Overview":
        show_overview()
    elif page == "Assignments":
        show_assignments()
    elif page == "Q&A":
        show_qa()
    elif page == "Document Manager":
        show_document_manager()
    elif page == "Download Manager":
        show_download_manager()
    elif page == "Settings":
        show_settings()

def show_overview():
    st.header("📊 Overview")
    
    # Load stats
    stats = load_assignment_stats()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Assignments", stats["total"])
    
    with col2:
        st.metric("Completed", stats["completed"])
    
    with col3:
        st.metric("Completion Rate", f"{stats['completion_rate']:.1f}%")
    
    with col4:
        # Check if ChromaDB exists
        chroma_exists = Path(config.CHROMA_PERSIST_DIRECTORY).exists()
        st.metric("Database Status", "✅ Ready" if chroma_exists else "❌ Not Setup")
    
    # Progress chart
    if stats["total"] > 0:
        fig = px.pie(
            values=[stats["completed"], stats["total"] - stats["completed"]],
            names=["Completed", "Pending"],
            title="Assignment Completion Status"
        )
        st.plotly_chart(fig)
    
    # Recent activity
    st.subheader("📝 Recent Activity")
    if stats["answer_files"]:
        recent_files = sorted(stats["answer_files"], key=os.path.getmtime, reverse=True)[:5]
        for file in recent_files:
            mod_time = datetime.fromtimestamp(os.path.getmtime(file))
            st.write(f"✅ {file.stem} - {mod_time.strftime('%Y-%m-%d %H:%M')}")
    else:
        st.info("No completed assignments yet.")

def show_assignments():
    st.header("📋 Assignment Manager")
    
    stats = load_assignment_stats()
    
    tab1, tab2 = st.tabs(["View Assignments", "Solve Assignment"])
    
    with tab1:
        st.subheader("📚 Available Assignments")
        
        if stats["assignment_files"]:
            assignment_data = []
            for file in stats["assignment_files"]:
                try:
                    content = file.read_text(encoding='utf-8')
                    has_answer = (config.ASSIGNMENT_ANSWERS_DIR / f"{file.stem}.txt").exists()
                    assignment_data.append({
                        "Assignment": file.stem,
                        "Preview": content[:100] + "..." if len(content) > 100 else content,
                        "Status": "✅ Completed" if has_answer else "⏳ Pending",
                        "File": str(file)
                    })
                except Exception as e:
                    st.error(f"Error reading {file.name}: {e}")
            
            df = pd.DataFrame(assignment_data)
            st.dataframe(df[["Assignment", "Preview", "Status"]], use_container_width=True)
            
            # Show assignment details
            selected_assignment = st.selectbox("Select assignment to view", [item["Assignment"] for item in assignment_data])
            if selected_assignment:
                selected_data = next(item for item in assignment_data if item["Assignment"] == selected_assignment)
                st.text_area("Assignment Content", utils.read_txt(Path(selected_data["File"])), height=200)
                
                # Show answer if exists
                answer_file = config.ASSIGNMENT_ANSWERS_DIR / f"{selected_assignment}.txt"
                if answer_file.exists():
                    st.subheader("📝 Generated Answer")
                    st.text_area("Answer", answer_file.read_text(encoding='utf-8'), height=300)
        else:
            st.info("No assignments found. Run the main pipeline to fetch assignments from Google Classroom.")
    
    with tab2:
        st.subheader("🧠 Auto-Solve Assignment")
        
        if stats["assignment_files"]:
            selected_file = st.selectbox(
                "Choose assignment to solve",
                [f.stem for f in stats["assignment_files"]]
            )
            
            if st.button("🚀 Solve Assignment"):
                try:
                    with st.spinner("Generating answer..."):
                        # Read assignment content
                        assignment_path = config.ASSIGNMENT_DIR / f"{selected_file}.txt"
                        content = assignment_path.read_text(encoding='utf-8')
                        
                        # Create assignment object
                        assignment = {
                            "title": selected_file,
                            "description": content
                        }
                        
                        # Import and use solve function
                        from assignment_handler import solve_assignment
                        answer_file = solve_assignment(assignment)
                        
                        st.success(f"✅ Assignment solved! Answer saved to {answer_file}")
                        
                        # Show the generated answer
                        answer_content = Path(answer_file).read_text(encoding='utf-8')
                        st.text_area("Generated Answer", answer_content, height=400)
                        
                except Exception as e:
                    st.error(f"Error solving assignment: {e}")
        else:
            st.info("No assignments available to solve.")

def show_qa():
    st.header("💬 Ask StudyMateAI")
    
    question = st.text_input("Ask a question about your course materials:")
    
    if st.button("🤔 Get Answer") and question:
        try:
            with st.spinner("Searching through your materials..."):
                # Import functions from main pipeline
                from studymateai_rag_pipeline import retrieve_chunks, ask_studymate
                
                context_chunks = retrieve_chunks(question)
                answer = ask_studymate(question, context_chunks)
                
                st.subheader("🤖 StudyMateAI's Answer:")
                st.write(answer)
                
                if context_chunks:
                    st.subheader("📚 Sources:")
                    for i, chunk in enumerate(context_chunks, 1):
                        with st.expander(f"Source {i}"):
                            st.write(chunk[:500] + "..." if len(chunk) > 500 else chunk)
                else:
                    st.info("Answer generated from general knowledge (no specific course materials found).")
                    
        except Exception as e:
            st.error(f"Error generating answer: {e}")

def show_document_manager():
    st.header("📁 Document Manager")
    
    tab1, tab2 = st.tabs(["Document Stats", "Upload Documents"])
    
    with tab1:
        st.subheader("📊 Document Statistics")
        
        # Count documents by type
        doc_stats = {}
        for doc_type, directory in config.DOWNLOAD_DIRS.items():
            if directory.exists():
                count = len(list(directory.glob("*")))
                doc_stats[doc_type] = count
        
        if doc_stats:
            df = pd.DataFrame(list(doc_stats.items()), columns=["Document Type", "Count"])
            st.dataframe(df)
            
            # Show pie chart
            fig = px.pie(df, values="Count", names="Document Type", title="Document Distribution")
            st.plotly_chart(fig)
        else:
            st.info("No documents found. Run the main pipeline to download materials.")
    
    with tab2:
        st.subheader("📤 Upload Documents")
        
        uploaded_file = st.file_uploader(
            "Upload a document",
            type=['pdf', 'docx', 'txt'],
            help="Upload additional study materials"
        )
        
        if uploaded_file and st.button("Upload"):
            try:
                # Determine directory based on file type
                file_ext = uploaded_file.name.split('.')[-1].lower()
                if file_ext == 'pdf':
                    target_dir = config.DOWNLOAD_DIRS['application/pdf']
                elif file_ext == 'docx':
                    target_dir = config.DOWNLOAD_DIRS['application/vnd.openxmlformats-officedocument.wordprocessingml.document']
                else:
                    target_dir = config.DATA_DIR / 'materials'
                
                target_dir.mkdir(parents=True, exist_ok=True)
                file_path = target_dir / uploaded_file.name
                
                with open(file_path, 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success(f"✅ File uploaded to {file_path}")
                
            except Exception as e:
                st.error(f"Error uploading file: {e}")

def show_download_manager():
    st.header("📥 Download Manager")
    
    instructions = utils.create_download_instructions()
    st.text_area("Manual Download Instructions", instructions, height=300)
    
    if st.button("✔️ Process Manual Downloads"):
        results = utils.process_manual_downloads()
        for name, result in results.items():
            st.write(f"{name}: {result}")


def show_settings():
    st.header("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🤖 AI Models")
        st.code(f"Embedding Model: {config.EMBEDDING_MODEL}")
        st.code(f"Chat Model: {config.CHAT_MODEL}")
        st.code(f"Chunk Size: {config.CHUNK_SIZE}")
        st.code(f"Chunk Overlap: {config.CHUNK_OVERLAP}")
    
    with col2:
        st.subheader("📁 Directories")
        st.code(f"Data Directory: {config.DATA_DIR}")
        st.code(f"Assignments: {config.ASSIGNMENT_DIR}")
        st.code(f"Answers: {config.ASSIGNMENT_ANSWERS_DIR}")
        st.code(f"ChromaDB: {config.CHROMA_PERSIST_DIRECTORY}")
    
    st.subheader("🔧 Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Database"):
            try:
                with st.spinner("Refreshing document database..."):
                    from studymateai_rag_pipeline import load_and_chunk_files, store_chunks
                    docs = load_and_chunk_files()
                    if docs:
                        store_chunks(docs)
                        st.success(f"✅ Refreshed database with {len(docs)} document chunks")
                    else:
                        st.warning("No documents found to process")
            except Exception as e:
                st.error(f"Error refreshing database: {e}")
    
    with col2:
        if st.button("📥 Sync Classroom"):
            try:
                with st.spinner("Syncing with Google Classroom..."):
                    from studymateai_rag_pipeline import authenticate_google, fetch_all_materials
                    creds = authenticate_google()
                    fetch_all_materials(creds)
                    st.success("✅ Classroom sync completed")
            except Exception as e:
                st.error(f"Error syncing classroom: {e}")
    
    with col3:
        if st.button("🧹 Clear Logs"):
            try:
                log_file = config.LOGS_DIR / "studymateai.log"
                if log_file.exists():
                    log_file.unlink()
                    st.success("✅ Logs cleared")
                else:
                    st.info("No logs to clear")
            except Exception as e:
                st.error(f"Error clearing logs: {e}")

if __name__ == "__main__":
    main()

