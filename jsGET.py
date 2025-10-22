import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
from flask import Flask, jsonify, request

# Load environment variables
load_dotenv()

# Get credentials from .env file
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

# Initialize Flask app
app = Flask(__name__)

def connect_to_gmail():
    """Connect to Gmail using IMAP"""
    try:
        # Connect to Gmail's IMAP server
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        
        # Login
        if EMAIL and PASSWORD:
            imap.login(EMAIL, PASSWORD)
            print(f"Successfully logged in as {EMAIL}")
        else:
            print("Email or password not found")
            return None
        
        return imap
    except Exception as e:
        print(f"Error connecting to Gmail: {e}")
        return None

def get_emails(imap, folder="INBOX", num_emails=10):
    """Fetch emails from specified folder and return as list"""
    emails_list = []
    
    try:
        # Select the mailbox (folder)
        status, messages = imap.select(folder)
        
        # Get total number of emails
        total_emails = int(messages[0])
        print(f"Total emails in {folder}: {total_emails}")
        
        # Fetch the last 'num_emails' emails
        start = max(1, total_emails - num_emails + 1)
        
        for i in range(total_emails, start - 1, -1):
            # Fetch the email by ID
            res, msg = imap.fetch(str(i), "(RFC822)")
            
            for response in msg:
                if isinstance(response, tuple):
                    # Parse the email content
                    msg = email.message_from_bytes(response[1])
                    
                    # Decode email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    
                    # Get sender
                    from_ = msg.get("From")
                    
                    # Get date
                    date = msg.get("Date")
                    
                    # Get email body
                    body_text = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            
                            try:
                                body = part.get_payload(decode=True)
                                if body and content_type == "text/plain" and "attachment" not in content_disposition:
                                    if isinstance(body, bytes):
                                        body_text = body.decode()
                                    else:
                                        body_text = str(body)
                                    break
                            except:
                                pass
                    else:
                        # Simple email
                        body = msg.get_payload(decode=True)
                        if body:
                            if isinstance(body, bytes):
                                body_text = body.decode()
                            else:
                                body_text = str(body)
                    
                    # Create email dict
                    email_data = {
                        "subject": subject,
                        "from": from_,
                        "date": date,
                        "body": body_text
                    }
                    
                    emails_list.append(email_data)
                    
                    # Print to console
                    print("\n" + "="*50)
                    print(f"Subject: {subject}")
                    print(f"From: {from_}")
                    print(f"Date: {date}")
                    print(f"Body: {body_text[:200]}...")
        
        print("\n" + "="*50)
        
    except Exception as e:
        print(f"Error fetching emails: {e}")
    
    return emails_list

@app.route('/receive', methods=['GET'])
def receive_emails():
    """API endpoint to receive emails"""
    if not EMAIL or not PASSWORD:
        return jsonify({"error": "EMAIL and PASSWORD must be set in .env file"}), 500
    
    # Get number of emails from query parameter (default: 10)
    num_emails = request.args.get('num', default=10, type=int)
    
    # Connect to Gmail
    imap = connect_to_gmail()
    
    if not imap:
        return jsonify({"error": "Failed to connect to Gmail"}), 500
    
    # Get emails from INBOX
    emails = get_emails(imap, folder="INBOX", num_emails=num_emails)
    
    # Close connection
    imap.close()
    imap.logout()
    print("\nDisconnected from Gmail")
    
    return jsonify({
        "success": True,
        "count": len(emails),
        "emails": emails
    })

@app.route('/', methods=['GET'])
def home():
    """Home endpoint"""
    return jsonify({
        "message": "Email Server API",
        "endpoints": {
            "/receive": "GET - Receive emails (query param: ?num=10)",
            "/send": "POST - Send 'HELLO WORLD' email (body: {\"to\": \"email@example.com\"})"
        }
    })

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
