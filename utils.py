"""
Utility functions for StudyMateAI
"""
import os
import logging
import pickle
import subprocess
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any
from rich.console import Console
from rich.progress import Progress, TaskID

# Optional imports with fallbacks
try:
    import fitz
except ImportError:
    fitz = None

try:
    from docx import Document
except ImportError:
    Document = None

try:
    from nltk.tokenize import sent_tokenize
except ImportError:
    sent_tokenize = None

import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOGS_DIR / "studymateai.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
console = Console()

class StudyMateAIError(Exception):
    """Base exception for StudyMateAI"""
    pass

class FileProcessingError(StudyMateAIError):
    """Exception for file processing errors"""
    pass

class APIError(StudyMateAIError):
    """Exception for API-related errors"""
    pass

def safe_filename(filename: str) -> str:
    """
    Convert filename to safe format for file system
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename[:255]  # Limit length

def read_pdf(file_path: Path) -> str:
    """
    Read PDF file and extract text
    """
    try:
        doc = fitz.open(str(file_path))
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    except Exception as e:
        logger.error(f"Error reading PDF {file_path}: {e}")
        raise FileProcessingError(f"Failed to read PDF: {e}")

def read_docx(file_path: Path) -> str:
    """
    Read DOCX file and extract text
    """
    try:
        doc = Document(str(file_path))
        return "\n".join([paragraph.text for paragraph in doc.paragraphs])
    except Exception as e:
        logger.error(f"Error reading DOCX {file_path}: {e}")
        raise FileProcessingError(f"Failed to read DOCX: {e}")

def read_txt(file_path: Path) -> str:
    """
    Read text file
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading TXT {file_path}: {e}")
        raise FileProcessingError(f"Failed to read TXT: {e}")

def chunk_text(text: str, chunk_size: int = config.CHUNK_SIZE, 
               overlap: int = config.CHUNK_OVERLAP) -> List[str]:
    """
    Enhanced text chunking with overlap
    """
    if not text.strip():
        return []
    
    try:
        sentences = sent_tokenize(text)
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = len(sentence.split())
            
            # If adding this sentence would exceed chunk size, save current chunk
            if current_tokens + sentence_tokens > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                
                # Keep last 'overlap' tokens for context
                overlap_sentences = []
                overlap_tokens = 0
                for sent in reversed(current_chunk):
                    sent_tokens = len(sent.split())
                    if overlap_tokens + sent_tokens <= overlap:
                        overlap_sentences.insert(0, sent)
                        overlap_tokens += sent_tokens
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_tokens = overlap_tokens
            
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
        
        # Add final chunk if it exists
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    except Exception as e:
        logger.error(f"Error chunking text: {e}")
        return [text]  # Return original text as fallback

def load_documents() -> List[Dict[str, Any]]:
    """
    Load and process all documents from data directory
    """
    documents = []
    file_processors = {
        '.pdf': read_pdf,
        '.docx': read_docx,
        '.txt': read_txt
    }
    
    with Progress() as progress:
        task = progress.add_task("Loading documents...", total=None)
        
        for root, _, files in os.walk(config.DATA_DIR):
            for file in files:
                file_path = Path(root) / file
                file_ext = file_path.suffix.lower()
                
                if file_ext in file_processors:
                    try:
                        text = file_processors[file_ext](file_path)
                        if text.strip():  # Only process non-empty files
                            chunks = chunk_text(text)
                            for i, chunk in enumerate(chunks):
                                documents.append({
                                    "id": f"{file}_{i}",
                                    "text": chunk,
                                    "source_file": file,
                                    "file_path": str(file_path),
                                    "chunk_index": i,
                                    "total_chunks": len(chunks)
                                })
                        progress.advance(task)
                    except FileProcessingError as e:
                        logger.warning(f"Skipping file {file_path}: {e}")
                        continue
    
    logger.info(f"Loaded {len(documents)} document chunks")
    return documents

def call_ollama(model: str, prompt: str, system_prompt: str = None) -> str:
    """
    Enhanced Ollama API call with better error handling
    """
    import subprocess  # Explicit import to avoid scope issues
    
    try:
        cmd = ["ollama", "run", model]
        
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt
        
        result = subprocess.run(
            cmd,
            input=full_prompt.encode('utf-8'),
            capture_output=True,
            timeout=60  # 1 minute timeout
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8')
            logger.error(f"Ollama error: {error_msg}")
            raise APIError(f"Ollama API error: {error_msg}")
        
        return result.stdout.decode('utf-8').strip()
    
    except subprocess.TimeoutExpired:
        logger.error("Ollama request timed out")
        raise APIError("Request timed out")
    except Exception as e:
        logger.error(f"Unexpected error calling Ollama: {e}")
        raise APIError(f"Failed to call Ollama: {e}")

def embed_text(text: str) -> Optional[List[float]]:
    """
    Generate embeddings for text using Ollama
    """
    try:
        prompt = f"Generate embeddings for: {text[:1000]}"  # Limit text length
        result = call_ollama(config.EMBEDDING_MODEL, prompt)
        
        # Try to parse the result as a list of floats
        # Note: This might need adjustment based on your embedding model's output format
        try:
            return eval(result.strip().splitlines()[-1])
        except:
            logger.warning(f"Could not parse embedding result: {result[:100]}...")
            return None
    
    except APIError as e:
        logger.error(f"Failed to generate embeddings: {e}")
        return None

def save_credentials(creds, filepath: Path = config.CREDENTIALS_DIR / "token.json"):
    """
    Save credentials to file
    """
    try:
        with open(filepath, 'wb') as token:
            pickle.dump(creds, token)
        logger.info(f"Credentials saved to {filepath}")
    except Exception as e:
        logger.error(f"Failed to save credentials: {e}")
        raise StudyMateAIError(f"Failed to save credentials: {e}")

def load_credentials(filepath: Path = config.CREDENTIALS_DIR / "token.json"):
    """
    Load credentials from file
    """
    try:
        if filepath.exists():
            with open(filepath, 'rb') as token:
                return pickle.load(token)
        return None
    except Exception as e:
        logger.error(f"Failed to load credentials: {e}")
        return None

def download_file_with_progress(url: str, filepath: Path, headers: dict = None) -> bool:
    """
    Download file with progress bar
    """
    try:
        response = requests.get(url, headers=headers, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        
        with open(filepath, 'wb') as file, Progress() as progress:
            task = progress.add_task(f"Downloading {filepath.name}", total=total_size)
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    progress.advance(task, len(chunk))
        
        logger.info(f"Downloaded {filepath.name}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to download {filepath.name}: {e}")
        return False

def format_assignment_prompt(title: str, description: str, context_chunks: List[str] = None) -> str:
    """
    Create a well-formatted prompt for assignment solving
    """
    context_section = ""
    if context_chunks:
        context_section = f"""
Relevant course materials:
{chr(10).join(f"- {chunk[:200]}..." for chunk in context_chunks)}

"""
    
    prompt = f"""You are StudyMateAI, an expert academic assistant. You must provide a complete, well-structured answer to the following assignment.

Assignment Title: {title}

Assignment Description: {description or 'No specific description provided.'}

{context_section}Instructions:
1. Provide a comprehensive answer that demonstrates deep understanding
2. Use proper academic formatting with clear sections and subsections
3. Include relevant examples, explanations, and analysis
4. Ensure your response is college-level quality
5. If the assignment asks for specific formats (essay, report, case study), follow those guidelines
6. Draw from both the provided materials and your general knowledge

Your answer should be complete and ready for submission. Do not ask for clarification or additional information.

Answer:"""
    
    return prompt

