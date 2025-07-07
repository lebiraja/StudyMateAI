
# 📚 StudyMateAI: Your Enhanced AI Classroom Assistant

**StudyMateAI** is a comprehensive AI-powered educational assistant designed to revolutionize how students manage their coursework. It seamlessly integrates with Google Classroom, intelligently processes course materials, and provides advanced assignment solving capabilities using local LLMs via Ollama.

---

## 🚀 Enhanced Features

### Core Features
✅ **Google Classroom Integration** - Seamless connection to your classroom  
✅ **Smart Document Processing** - Handles PDFs, DOCX, videos, images, and more  
✅ **Advanced Assignment Analysis** - Intelligent assignment retrieval and processing  
✅ **RAG-based Q&A System** - Context-aware question answering  
✅ **Vector Database Storage** - Fast semantic search with ChromaDB   
✅ **Local LLM Processing** - Privacy-focused AI with Ollama integration  
✅ **Assignment Auto-Solving** - Complete assignment generation with enhanced prompts  
✅ **Automatic Submission** - Direct submission to Google Classroom  

### New Enhancements
🆕 **Streamlit Dashboard** - Beautiful web interface for easy interaction  
🆕 **Enhanced Error Handling** - Robust error management and logging  
🆕 **Configuration Management** - Centralized config with easy customization  
🆕 **Rich CLI Interface** - Beautiful terminal output with progress bars  
🆕 **Improved Prompt Engineering** - Better assignment solving with fallback strategies  
🆕 **Setup Automation** - One-click setup script for easy installation  
🆕 **Document Upload** - Manual document upload through web interface

---

## 🧠 Tech Stack

| Component            | Tool / Tech                            |
|----------------------|----------------------------------------|
| Authentication       | Google OAuth 2.0 (`google-auth-oauthlib`) |
| APIs                 | Google Classroom, Google Drive         |
| Embedding Model      | `bge-m3` via Ollama                    |
| Language Model       | Custom Ollama model: `studymateai`     |
| Vector Store         | ChromaDB                               |
| Document Parsing     | PyMuPDF, python-docx, requests         |
| NLP                  | NLTK                                   |
| Future UI            | Streamlit or Flask                     |
| Telegram Bot         | Telegram Bot API (WIP)                 |

---

## 📁 Project Structure

```bash
studymateai/
│
├── data/
│   ├── pdfs/                # Downloaded PDFs
│   ├── docs/                # Downloaded DOCX files
│   ├── materials/           # Videos, images, PPTs
│   ├── answers/             # Auto-solved assignment answers
│   └── embeddings/          # Optional: Store Chroma data
│
├── credentials/
│   └── client_secret.json   # Google API OAuth secret
│
├── scripts/
│   ├── fetch_materials.py         # Downloads all course materials
│   ├── fetch_assignments.py       # Lists and fetches all assignments
│   ├── embedding_engine.py        # Embeds documents to ChromaDB
│   ├── ask_engine.py              # Q&A system using Ollama + context
│   ├── solve_assignment.py        # Auto-solves assignments using LLM
│   ├── submit_assignment.py       # (🔜) Auto-submits to Classroom
│   ├── telegram_notifier.py       # (🔜) Sends Telegram alerts
│   └── utils.py                   # Shared chunking/parsing utilities
│
├── studymateai_rag_pipeline.py    # Main pipeline (materials + Q&A)
├── assignment_handler.py          # Assignment-solving pipeline
│
├── .env                           # (🔜) API keys and secrets
├── requirements.txt
└── README.md
````

---

## 🧩 How It Works

1. **Google Authentication** using OAuth 2.0
2. **Fetches materials** from Google Classroom and Drive
3. **Parses PDFs and DOCX** using PyMuPDF and `python-docx`
4. **Chunks & embeds** using NLTK + Ollama (`bge-m3`)
5. **Stores in ChromaDB** for semantic retrieval
6. **Queries the system** using your questions
7. **Answers** using Ollama (`studymateai`) with or without file context
8. **Assignment Flow**:

   * Lists assignments
   * Matches materials (if available)
   * Generates answers using fallback
   * (🔜) Submits answers to Google Classroom



---

## ⚙️ Quick Setup

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai) installed and running
- Google Cloud Project with Classroom/Drive APIs enabled

### Installation

1. **Clone and navigate to the project:**
```bash
cd studymateai
```

2. **Run the automated setup:**
```bash
python setup.py
```

3. **Manual Google API setup (if needed):**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Enable Google Classroom and Drive APIs
   - Create OAuth 2.0 credentials
   - Download as `client_secret.json`
   - Place in the project root directory

4. **Install required Ollama models:**
```bash
ollama pull bge-m3
ollama pull studymateai  # or your preferred model
```

### Usage Options

**Option 1: Web Dashboard (Recommended)**
```bash
streamlit run dashboard.py
```

**Option 2: Command Line Interface**
```bash
# Main RAG pipeline
python studymateai_rag_pipeline.py

# Assignment handler
python assignment_handler.py
```

---

## 💬 Example Usage

**Ask a question:**

```bash
📩 Your question: what is iot
🤖 StudyMateAI says:
"IoT refers to..."
```

**Solve an assignment:**

```bash
python assignment_handler.py
📩 Auto-solving: Case Study on Smart Home Connectivity
🤖 Answer saved to: data/answers/SmartHome_case_study.txt
```

---

## 🌐 Planned Features

* [x] Assignment auto-solving even if file is missing
* [ ] Auto-submit assignments to Classroom
* [ ] Notify via Telegram
* [ ] Add course-specific AI profiles
* [ ] Web dashboard for easier usage (Streamlit)

---

```
