import os
from pathlib import Path
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from rich.console import Console
from rich.progress import Progress
from studymateai_rag_pipeline import retrieve_chunks, ask_studymate

# Import enhanced modules
import config
import utils
from utils import logger, StudyMateAIError

console = Console()

def list_assignments(creds):
    classroom = build('classroom', 'v1', credentials=creds)
    courses = classroom.courses().list().execute().get('courses', [])
    assignments = []

    for course in courses:
        try:
            course_id = course['id']
            course_name = course['name']
            course_work = classroom.courses().courseWork().list(courseId=course_id).execute().get('courseWork', [])
            for work in course_work:
                if work['workType'] == 'ASSIGNMENT':
                    assignments.append({
                        'courseId': course_id,
                        'courseName': course_name,
                        'id': work['id'],
                        'title': work['title'],
                        'description': work.get('description', ''),
                        'dueDate': work.get('dueDate', {}),
                        'state': work.get('state', 'UNKNOWN')
                    })
        except Exception as e:
            print(f"⚠️ Could not fetch assignments from {course['name']}: {e}")

    return assignments

def solve_assignment(assignment):
    """Enhanced assignment solving with better prompting and error handling"""
    try:
        title = assignment['title']
        description = assignment.get('description', '')
        
        logger.info(f"Solving assignment: {title}")
        console.print(f"🧠 Solving: {title}", style="blue")
        
        # Try to find relevant context first
        context_chunks = retrieve_chunks(f"{title} {description}")
        
        # Use enhanced prompt formatting
        prompt = utils.format_assignment_prompt(title, description, context_chunks)
        
        # Generate the answer
        with console.status("[bold green]Generating answer..."):
            answer = utils.call_ollama(config.CHAT_MODEL, prompt)
        
        # Save the answer with safe filename
        safe_title = utils.safe_filename(title)
        filename = f"{safe_title}.txt"
        filepath = config.ASSIGNMENT_ANSWERS_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(answer)
        
        logger.info(f"Answer saved to {filepath}")
        console.print(f"✅ Answer saved to {filepath}", style="green")
        return filepath
        
    except Exception as e:
        logger.error(f"Failed to solve assignment '{title}': {e}")
        console.print(f"❌ Failed to solve assignment: {e}", style="red")
        raise StudyMateAIError(f"Assignment solving failed: {e}")

def upload_to_drive(creds, filepath):
    drive = build('drive', 'v3', credentials=creds)
    file_metadata = {'name': os.path.basename(filepath)}
    media = MediaFileUpload(filepath, resumable=True)
    uploaded_file = drive.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return uploaded_file['id']

def submit_assignment(creds, course_id, assignment_id, filepath):
    classroom = build('classroom', 'v1', credentials=creds)

    student_subs = classroom.courses().courseWork().studentSubmissions()
    subs = student_subs.list(courseId=course_id, courseWorkId=assignment_id).execute()

    if not subs.get('studentSubmissions'):
        print("❌ No student submission found.")
        return

    submission_id = subs['studentSubmissions'][0]['id']
    print("📤 Uploading answer to Drive...")
    drive_file_id = upload_to_drive(creds, filepath)

    print("📎 Attaching file to assignment submission...")
    student_subs.modifyAttachments(
        courseId=course_id,
        courseWorkId=assignment_id,
        id=submission_id,
        body={
            "addAttachments": [
                {"driveFile": {"id": drive_file_id}}
            ]
        }
    ).execute()

    print("📨 Turning in submission...")
    student_subs.turnIn(courseId=course_id, courseWorkId=assignment_id, id=submission_id).execute()
    print("✅ Assignment submitted successfully!")

if __name__ == "__main__":
    try:
        from studymateai_rag_pipeline import authenticate_google
        
        console.print("🔐 Authenticating with Google...", style="blue")
        creds = authenticate_google()
        
        console.print("📋 Listing assignments...", style="blue")
        assignments = list_assignments(creds)
        
        if not assignments:
            console.print("ℹ️ No assignments found.", style="yellow")
            exit()
        
        console.print("\n📚 Available Assignments:", style="bold blue")
        for i, a in enumerate(assignments):
            console.print(f"[{i}] {a['title']} (Course: {a['courseName']})")
        
        try:
            choice = int(input("\n📌 Choose assignment to auto-solve (number): "))
            if choice < 0 or choice >= len(assignments):
                console.print("❌ Invalid choice!", style="red")
                exit()
            
            selected = assignments[choice]
            
            console.print(f"\n🧠 Generating answer for: {selected['title']}", style="green")
            answer_file = solve_assignment(selected)
            
            # Ask if user wants to submit
            submit_choice = input("\n🚀 Do you want to submit this to Google Classroom? (y/n): ")
            if submit_choice.lower() == 'y':
                console.print("📤 Submitting answer to Classroom...", style="blue")
                submit_assignment(creds, selected['courseId'], selected['id'], str(answer_file))
            else:
                console.print("💾 Answer saved locally. You can manually review and submit later.", style="green")
                
        except ValueError:
            console.print("❌ Please enter a valid number!", style="red")
        except KeyboardInterrupt:
            console.print("\n👋 Operation cancelled by user.", style="yellow")
            
    except Exception as e:
        logger.error(f"Assignment handler failed: {e}")
        console.print(f"❌ Error: {e}", style="red")
