import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta

# Define the scopes for Gmail access
GCLOUD_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def gmail_authenticate():
    creds = None
    # Check if token.pickle file exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If credentials are not valid or don't exist, create new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('ajaytestinbox_token.json', GCLOUD_SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def get_unread_emails(service, user_id='me'):
    one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).strftime('%Y/%m/%d')
    # query = f'is:unread after:{one_hour_ago}'
    query = f'is:unread has:attachment'
    
    try:
        results = service.users().messages().list(userId=user_id, q=query).execute()
        messages = results.get('messages', [])
        
        for message in messages:
            msg = service.users().messages().get(userId=user_id, id=message['id']).execute()
            email_data = msg['payload']['headers']
            subject = next(item for item in email_data if item["name"] == "Subject")
            sender = next(item for item in email_data if item["name"] == "From")
            print(f"From: {sender['value']}")
            print(f"Subject: {subject['value']}")
            print("Snippet:", msg['snippet'])
            print("------------------------")
        
        if not messages:
            print("No email matching the search criteria.")
    
    except Exception as error:
        print(f'An error occurred: {error}')

def main():
    # Authenticate and get the Gmail service
    service = gmail_authenticate()
    
    # # Example: List the user's Gmail labels
    # results = service.users().labels().list(userId='me').execute()
    # labels = results.get('labels', [])

    # if not labels:
    #     print('No labels found.')
    # else:
    #     print('Labels:')
    #     for label in labels:
    #         print(label['name'])
    
    # Listing out the unread messages
    get_unread_emails(service)

if __name__ == '__main__':
    main()
