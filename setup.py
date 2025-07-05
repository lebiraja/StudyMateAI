"""
StudyMateAI Setup Script
"""
import subprocess
import sys
import os
from pathlib import Path
import nltk
from rich.console import Console
from rich.progress import Progress
import config

console = Console()

def install_requirements():
    """Install required packages"""
    console.print("📦 Installing required packages...", style="blue")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        console.print("✅ Requirements installed successfully", style="green")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"❌ Failed to install requirements: {e}", style="red")
        return False

def setup_nltk():
    """Download required NLTK data"""
    console.print("📚 Setting up NLTK data...", style="blue")
    
    try:
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        console.print("✅ NLTK data downloaded", style="green")
        return True
    except Exception as e:
        console.print(f"❌ Failed to setup NLTK: {e}", style="red")
        return False

def create_directories():
    """Create necessary directories"""
    console.print("📁 Creating project directories...", style="blue")
    
    try:
        # Directories are already created by config.py
        console.print("✅ Directories created", style="green")
        return True
    except Exception as e:
        console.print(f"❌ Failed to create directories: {e}", style="red")
        return False

def check_ollama():
    """Check if Ollama is installed and running"""
    console.print("🤖 Checking Ollama installation...", style="blue")
    
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode == 0:
            console.print("✅ Ollama is installed and running", style="green")
            
            # Check for required models
            models = result.stdout
            required_models = [config.EMBEDDING_MODEL, config.CHAT_MODEL]
            missing_models = []
            
            for model in required_models:
                if model not in models:
                    missing_models.append(model)
            
            if missing_models:
                console.print(f"⚠️ Missing models: {', '.join(missing_models)}", style="yellow")
                console.print("Run the following commands to install missing models:", style="yellow")
                for model in missing_models:
                    console.print(f"  ollama pull {model}", style="cyan")
                return False
            else:
                console.print("✅ All required models are available", style="green")
                return True
        else:
            console.print("❌ Ollama is not running or not installed", style="red")
            console.print("Please install Ollama from https://ollama.ai", style="yellow")
            return False
    except FileNotFoundError:
        console.print("❌ Ollama is not installed", style="red")
        console.print("Please install Ollama from https://ollama.ai", style="yellow")
        return False

def check_credentials():
    """Check if Google credentials are available"""
    console.print("🔐 Checking Google credentials...", style="blue")
    
    client_secret_path = config.CREDENTIALS_DIR / "client_secret.json"
    if client_secret_path.exists():
        console.print("✅ Google credentials found", style="green")
        return True
    else:
        console.print("❌ Google credentials not found", style="red")
        console.print(f"Please place your client_secret.json file in {config.CREDENTIALS_DIR}", style="yellow")
        console.print("Instructions:", style="yellow")
        console.print("1. Go to Google Cloud Console", style="cyan")
        console.print("2. Enable Google Classroom and Drive APIs", style="cyan")
        console.print("3. Create OAuth 2.0 credentials", style="cyan")
        console.print("4. Download the JSON file as 'client_secret.json'", style="cyan")
        return False

def main():
    """Main setup function"""
    console.print("🚀 StudyMateAI Setup", style="bold blue")
    console.print("="*50, style="blue")
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Install requirements
    if install_requirements():
        success_count += 1
    
    # Step 2: Setup NLTK
    if setup_nltk():
        success_count += 1
    
    # Step 3: Create directories
    if create_directories():
        success_count += 1
    
    # Step 4: Check Ollama
    if check_ollama():
        success_count += 1
    
    # Step 5: Check credentials
    if check_credentials():
        success_count += 1
    
    console.print("\n" + "="*50, style="blue")
    console.print(f"Setup completed: {success_count}/{total_steps} steps successful", 
                  style="green" if success_count == total_steps else "yellow")
    
    if success_count == total_steps:
        console.print("\n🎉 StudyMateAI is ready to use!", style="bold green")
        console.print("\nNext steps:", style="blue")
        console.print("1. Run: python studymateai_rag_pipeline.py", style="cyan")
        console.print("2. Or start the dashboard: streamlit run dashboard.py", style="cyan")
    else:
        console.print("\n⚠️ Please complete the failed steps before using StudyMateAI", style="yellow")

if __name__ == "__main__":
    main()

