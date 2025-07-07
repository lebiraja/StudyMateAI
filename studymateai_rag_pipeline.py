# studymateai_rag_pipeline.py
import os
import pickle
import requests
import nltk
from typing import List, Optional
from rich.console import Console
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import chromadb
import fitz
from docx import Document
from nltk.tokenize import sent_tokenize

# Import our enhanced modules
import config
import utils
from utils import logger, StudyMateAIError, APIError

nltk.download('punkt', quiet=True)
console = Console()

def authenticate_google():
    """Enhanced Google authentication with better error handling"""
    try:
        creds = utils.load_credentials()
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired credentials...")
                creds.refresh(Request())
            else:
                logger.info("Starting new authentication flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(config.CREDENTIALS_DIR / 'client_secret.json'), 
                    config.SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            utils.save_credentials(creds)
        
        logger.info("✅ Google authentication successful")
        return creds
    
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise StudyMateAIError(f"Failed to authenticate with Google: {e}")

def download_file(service, file_id, file_name, mime_type, token):
    """Enhanced file download with better error handling and alternatives"""
    try:
        directory = config.DOWNLOAD_DIRS.get(mime_type, config.DATA_DIR / 'materials')
        directory.mkdir(parents=True, exist_ok=True)
        
        ext = config.EXTENSION_MAP.get(mime_type, '.bin')
        safe_name = utils.safe_filename(file_name)
        file_path = directory / (safe_name + ext)

        # Check if file already exists
        if file_path.exists():
            logger.info(f"📄 File already exists: {safe_name + ext}")
            console.print(f"📄 File already exists: {safe_name + ext}", style="yellow")
            return

        # Method 1: Try direct download
        success = False
        try:
            if mime_type == 'application/vnd.google-apps.document':
                request = service.files().export_media(
                    fileId=file_id,
                    mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
            else:
                request = service.files().get_media(fileId=file_id)

            response = requests.get(request.uri, headers={"Authorization": f"Bearer {token}"}, timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"📄 Downloaded: {safe_name + ext} to {directory}")
            console.print(f"📄 Downloaded: {safe_name + ext}", style="green")
            success = True
            
        except Exception as direct_error:
            logger.warning(f"Direct download failed for {file_name}: {direct_error}")
            
            # Method 2: Try using Drive API's get method with alt=media
            try:
                file_metadata = service.files().get(fileId=file_id, fields='webContentLink,webViewLink,exportLinks').execute()
                
                # Try webContentLink first
                if 'webContentLink' in file_metadata:
                    download_url = file_metadata['webContentLink']
                    response = requests.get(download_url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
                    response.raise_for_status()
                    
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    
                    logger.info(f"📄 Downloaded via webContentLink: {safe_name + ext}")
                    console.print(f"📄 Downloaded via webContentLink: {safe_name + ext}", style="green")
                    success = True
                    
                elif 'exportLinks' in file_metadata and mime_type == 'application/vnd.google-apps.document':
                    # For Google Docs, try export links
                    export_mime = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    if export_mime in file_metadata['exportLinks']:
                        export_url = file_metadata['exportLinks'][export_mime]
                        response = requests.get(export_url, headers={"Authorization": f"Bearer {token}"}, timeout=30)
                        response.raise_for_status()
                        
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"📄 Downloaded via export link: {safe_name + ext}")
                        console.print(f"📄 Downloaded via export link: {safe_name + ext}", style="green")
                        success = True
                        
            except Exception as alt_error:
                logger.warning(f"Alternative download failed for {file_name}: {alt_error}")
        
        # Method 3: Create a placeholder file with metadata if download fails
        if not success:
            try:
                file_metadata = service.files().get(fileId=file_id, fields='name,mimeType,size,webViewLink,description').execute()
                placeholder_content = f"""FILE DOWNLOAD FAILED
===================

Original filename: {file_name}
File ID: {file_id}
MIME Type: {mime_type}
Web View Link: {file_metadata.get('webViewLink', 'Not available')}
Description: {file_metadata.get('description', 'No description')}

This file could not be downloaded automatically. You can:
1. Access it directly via the web view link above
2. Download it manually from Google Drive
3. Check if you have proper permissions to access this file

To manually download:
1. Visit the web view link above
2. Click "File" → "Download" in Google Drive
3. Save the file to: {file_path}"""
                
                placeholder_path = directory / (safe_name + '_PLACEHOLDER.txt')
                with open(placeholder_path, 'w', encoding='utf-8') as f:
                    f.write(placeholder_content)
                
                logger.warning(f"📄 Created placeholder for failed download: {safe_name}_PLACEHOLDER.txt")
                console.print(f"📄 Created placeholder for failed download: {safe_name}_PLACEHOLDER.txt", style="yellow")
                
            except Exception as placeholder_error:
                logger.error(f"Failed to create placeholder for {file_name}: {placeholder_error}")
        
    except Exception as e:
        logger.error(f"Complete download failure for {file_name}: {e}")
        console.print(f"❌ Complete download failure for {file_name}: {e}", style="red")

def fetch_all_materials(creds):
    classroom = build('classroom', 'v1', credentials=creds)
    drive = build('drive', 'v3', credentials=creds)
    token = creds.token
    courses = classroom.courses().list().execute().get('courses', [])
    for course in courses:
        print(f"\n📘 Course: {course['name']}")
        course_id = course['id']
        try:
            coursework = classroom.courses().courseWork().list(courseId=course_id).execute().get('courseWork', [])
            for work in coursework:
                if 'materials' in work:
                    for mat in work['materials']:
                        drive_file = mat.get('driveFile', {}).get('driveFile')
                        if drive_file:
                            file_id = drive_file['id']
                            file_name = drive_file['title']
                            mime = drive.files().get(fileId=file_id, fields='mimeType').execute().get('mimeType')
                            download_file(drive, file_id, file_name, mime, token)
        except HttpError as e:
            print(f"⚠️ Could not fetch materials for {course['name']}: {e}")

def read_docx(path):
    doc = Document(path)
    return "\n".join(p.text for p in doc.paragraphs)

def load_and_chunk_files():
    documents = []
    for root, _, files in os.walk("data"):
        for file in files:
            path = os.path.join(root, file)
            if file.lower().endswith(".pdf"):
                text = "".join([page.get_text() for page in fitz.open(path)])
            elif file.lower().endswith(".docx"):
                text = read_docx(path)
            else:
                continue
            sents = sent_tokenize(text)
            chunk, chunks, tokens = [], [], 0
            for sent in sents:
                wc = len(sent.split())
                if tokens + wc > 500:
                    chunks.append(" ".join(chunk))
                    chunk = chunk[-50:]
                    tokens = sum(len(s.split()) for s in chunk)
                chunk.append(sent)
                tokens += wc
            if chunk:
                chunks.append(" ".join(chunk))
            for i, c in enumerate(chunks):
                documents.append({"id": f"{file}_{i}", "text": c, "source_file": file})
    return documents

def embed_text(text):
    import subprocess
    prompt = f"Return a dense vector embedding of this text:\n{text}"
    result = subprocess.run(["ollama", "run", "bge-m3"], input=prompt.encode(), capture_output=True)
    try:
        return eval(result.stdout.decode().strip().splitlines()[-1])
    except:
        return None

def store_chunks(docs):
    client = chromadb.Client()
    collection = client.get_or_create_collection("studymate")
    for doc in docs:
        emb = embed_text(doc["text"])
        if emb:
            collection.add(documents=[doc["text"]], metadatas=[{"file": doc["source_file"]}],
                           ids=[doc["id"]], embeddings=[emb])
    print("✅ Stored chunks in ChromaDB.")

def retrieve_chunks(query):
    emb = embed_text(query)
    if not emb:
        return []
    collection = chromadb.Client().get_or_create_collection("studymate")
    result = collection.query(query_embeddings=[emb], n_results=3)
    return result["documents"][0] if result["documents"] else []

def ask_studymate(query, context_chunks):
    import subprocess
    context = "\n\n".join(context_chunks)
    prompt = f"""You are StudyMateAI, an AI tutor for students. Use the following documents only as references.
Answer the question with your own knowledge. If the context helps, you may use it to enrich your answer.

---Context---
{context}
--------------

Question: {query}
Answer:"""
    result = subprocess.run(["ollama", "run", "studymateai"], input=prompt.encode(), capture_output=True)
    return result.stdout.decode().strip()

if __name__ == "__main__":
    print("🔐 Authenticating with Google...")
    creds = authenticate_google()

    print("\n📥 Fetching classroom files...")
    fetch_all_materials(creds)

    print("\n📚 Loading and chunking materials...")
    docs = load_and_chunk_files()
    print(f"✅ Loaded {len(docs)} chunks.")

    if docs:
        print("\n🧠 Storing in ChromaDB...")
        store_chunks(docs)

    print("\n💬 Ask your question:")
    question = input("📩 Your question: ")
    context = retrieve_chunks(question)

    print("\n🤖 StudyMateAI says:\n")
    print(ask_studymate(question, context))
