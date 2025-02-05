import os
import pickle
import base64
import re
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from PyPDF2 import PdfReader
from google.cloud import language_v1

GCLOUD_SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "nlp_key.json"

def gmail_authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('ajaytestinbox_token.json', GCLOUD_SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            text = "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        return text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

# def parse_transaction_details(text):
#     transactions = []
#     pattern = re.compile(r'(?P<description>.+?)\s+(?P<amount>\d+\.\d{2})')
#     for match in pattern.finditer(text):
#         transactions.append(match.groupdict())
#     return transactions




def google_nlp_extract(text):
    """ Uses Google Cloud NLP to extract transaction descriptions and amounts. """
    client = language_v1.LanguageServiceClient()
    
    document = language_v1.Document(content=text, type_=language_v1.Document.Type.PLAIN_TEXT)
    response = client.analyze_entities(request={"document": document})

    transactions = []
    
    for entity in response.entities:
        #print("Inside the NLP function")
        print(entity.type_)
        if entity.type_ == language_v1.Entity.Type.PRICE and '$' in entity.name:
            amount = entity.name  # Extract the amount
            # Find the closest description (assumes description appears near the number)
            description = entity.metadata.get("wikipedia_url", "Transaction")  # Default fallback
            
            transactions.append({"description": description, "amount": amount})
    
    return transactions


def get_unread_emails_with_pdfs(service, user_id='me'):
    query = 'is:unread has:attachment'
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
            
            for part in msg['payload'].get('parts', []):
                if part['filename'].endswith('.pdf'):
                    attachment_id = part['body']['attachmentId']
                    attachment = service.users().messages().attachments().get(userId=user_id, messageId=message['id'], id=attachment_id).execute()
                    data = base64.urlsafe_b64decode(attachment['data'])
                    pdf_path = part['filename']
                    
                    with open(pdf_path, 'wb') as f:
                        f.write(data)
                    
                    print(f"Downloaded PDF: {pdf_path}")
                    
                    text = extract_text_from_pdf(pdf_path)
                    # transactions = parse_transaction_details(text)
                    transactions = google_nlp_extract(text)
                    
                    if transactions:
                        print("Extracted Transactions:")
                        for txn in transactions:
                            print(f"Description: {txn['description']}, Amount: {txn['amount']}")
                    else:
                        print("No transactions found in the PDF.")
                    
                    os.remove(pdf_path)
                    print("PDF deleted after processing.")
            
            print("------------------------")
        
        if not messages:
            print("No email matching the search criteria.")
    except Exception as error:
        print(f'An error occurred: {error}')

def main():
    service = gmail_authenticate()
    get_unread_emails_with_pdfs(service)

if __name__ == '__main__':
    main()
