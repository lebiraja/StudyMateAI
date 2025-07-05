from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/classroom.courses.readonly']

flow = InstalledAppFlow.from_client_secrets_file(
    'client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)

service = build('classroom', 'v1', credentials=creds)

# Get list of courses
results = service.courses().list().execute()
courses = results.get('courses', [])

for course in courses:
    print(f"{course['name']} (ID: {course['id']})")
