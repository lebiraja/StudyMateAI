#!/usr/bin/env python3
"""
Manual Download Helper for StudyMateAI

This script helps users manage files that couldn't be downloaded automatically
from Google Drive due to permission or access issues.
"""

import os
import sys
from pathlib import Path

# Add the project directory to the path
sys.path.append(str(Path(__file__).parent))

import config
import utils
from utils import logger, console

def main():
    """Main function to help with manual downloads"""
    
    console.print("📥 StudyMateAI Manual Download Helper", style="bold blue")
    console.print("=" * 50)
    
    # Check for placeholder files
    placeholder_files = utils.find_placeholder_files()
    
    if not placeholder_files:
        console.print("✅ No files need manual download!", style="green")
        console.print("All course materials have been downloaded successfully.")
        return
    
    console.print(f"Found {len(placeholder_files)} files that need manual download", style="yellow")
    console.print()
    
    # Display instructions
    instructions = utils.create_download_instructions()
    console.print(instructions)
    
    # Ask user if they want to process downloads
    console.print()
    console.print("After manually downloading files, run this script again to process them.", style="cyan")
    
    # Check if user has downloaded any files
    response = input("\nHave you manually downloaded any files? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        console.print("\n🔄 Processing manual downloads...", style="blue")
        results = utils.process_manual_downloads()
        
        if results:
            console.print("\n📊 Processing Results:", style="bold")
            for name, result in results.items():
                if "Found manually downloaded file" in result:
                    console.print(f"✅ {name}: {result}", style="green")
                else:
                    console.print(f"⚠️  {name}: {result}", style="yellow")
        else:
            console.print("No manual downloads were processed.", style="yellow")
    
    console.print("\n📝 Tips for manual downloads:", style="bold")
    console.print("1. Open the Google Drive links provided above")
    console.print("2. Click 'File' → 'Download' in Google Drive")
    console.print("3. Save files to the exact paths specified")
    console.print("4. Run this script again to process the downloads")
    console.print("5. Use the StudyMateAI dashboard for a graphical interface")

def show_status():
    """Show the current download status"""
    console.print("📊 Download Status", style="bold blue")
    console.print("=" * 30)
    
    placeholder_files = utils.find_placeholder_files()
    
    if not placeholder_files:
        console.print("✅ All files downloaded successfully!", style="green")
        return
    
    console.print(f"Files pending manual download: {len(placeholder_files)}", style="yellow")
    
    for i, placeholder_path in enumerate(placeholder_files, 1):
        try:
            with open(placeholder_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract original filename
            original_name = "Unknown"
            for line in content.split('\n'):
                if line.startswith('Original filename:'):
                    original_name = line.split(':', 1)[1].strip()
                    break
            
            console.print(f"{i}. {original_name}", style="cyan")
            
        except Exception as e:
            console.print(f"{i}. Error reading placeholder: {placeholder_path}", style="red")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_status()
    else:
        main()

