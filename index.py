import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
import time
import threading
from dotenv import load_dotenv
from ai_service import email_ai_response
from flask import Flask, jsonify, request

# Load environment variables
load_dotenv()

# Get credentials from .env file
EMAIL = os.getenv('EMAIL')
PASSWORD = os.getenv('PASSWORD')

# Initialize Flask app
app = Flask(__name__)

# Ensure logs directory exists
os.makedirs('./logs', exist_ok=True)

ALL_MAIL_FILE = './logs/AllMail.json'
UNREAD_MAIL_FILE = './logs/UnreadMail.json'
RESPONDED_MAIL_FILE = './logs/RespondedMail.json'

def connect_to_gmail():
    """Connect to Gmail using IMAP"""
    try:
        # Connect to Gmail's IMAP server
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        
        # Login
        if EMAIL and PASSWORD:
            imap.login(EMAIL, PASSWORD)
        else:
            print("ERROR: Email or password not found")
            return None
        
        return imap
    except Exception as e:
        print(f"ERROR connecting to Gmail: {e}")
        return None

def get_emails(imap, folder="INBOX", num_emails=10, only_unread=False):
    """Fetch emails from specified folder and return as list"""
    emails_list = []
    
    try:
        # Select the mailbox (folder)
        status, messages = imap.select(folder)
        
        # Search for emails based on read/unread status
        if only_unread:
            # Search for unread emails
            status, email_ids = imap.search(None, 'UNSEEN')
        else:
            # Get all emails
            status, email_ids = imap.search(None, 'ALL')
        
        # Convert to list of IDs
        email_id_list = email_ids[0].split()
        
        if not email_id_list:
            return []
        
        # Get the last 'num_emails' or all unread emails
        if only_unread:
            # For unread, get all of them
            ids_to_fetch = email_id_list
        else:
            # For all emails, get the last num_emails
            ids_to_fetch = email_id_list[-num_emails:] if len(email_id_list) > num_emails else email_id_list
        
        for email_id in reversed(ids_to_fetch):
            # Fetch the email by ID
            res, msg = imap.fetch(email_id, "(RFC822)")
            
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
                    
                    # Get Message-ID for unique identification
                    message_id = msg.get("Message-ID")
                    
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
                        "message_id": message_id,
                        "subject": subject,
                        "from": from_,
                        "date": date,
                        "body": body_text
                    }
                    
                    emails_list.append(email_data)
        
    except Exception as e:
        print(f"ERROR fetching emails: {e}")
    
    return emails_list

def send_email(to_email, subject, body):
    """Send email using SMTP"""
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL # type: ignore
        msg['To'] = to_email
        msg['Subject'] = f"Re: {subject}"
        
        # Attach body
        msg.attach(MIMEText(body, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        if EMAIL and PASSWORD:
            server.login(EMAIL, PASSWORD)
        else:
            print("ERROR: Email or password not found")
            return False
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"ERROR sending email: {e}")
        return False

def load_json_file(filepath):
    """Load JSON file, return empty list if file doesn't exist"""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"ERROR loading {filepath}: {e}")
        return []

def save_json_file(filepath, data):
    """Save data to JSON file"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"ERROR saving to {filepath}: {e}")

def fetch_emails_thread():
    """Thread 1: Continuously fetch emails and save to AllMail.json and UnreadMail.json"""
    
    while True:
        try:
            # Connect to Gmail
            imap = connect_to_gmail()
            
            if imap:
                # Load existing AllMail data
                existing_all_mails = load_json_file(ALL_MAIL_FILE)
                existing_message_ids = {mail.get('message_id') for mail in existing_all_mails if mail.get('message_id')}
                
                # Get all emails from INBOX
                all_emails = get_emails(imap, folder="INBOX", num_emails=10, only_unread=False)
                
                # Find new emails (not in AllMail.json)
                unread_emails = []
                for email_data in all_emails:
                    if email_data.get('message_id') not in existing_message_ids:
                        unread_emails.append(email_data)
                
                # Save all emails to AllMail.json
                save_json_file(ALL_MAIL_FILE, all_emails)
                
                # Save only new emails to UnreadMail.json
                save_json_file(UNREAD_MAIL_FILE, unread_emails)
                
                # Close connection
                imap.close()
                imap.logout()
                
            # Wait before next fetch (e.g., 60 seconds)
            time.sleep(60)
            
        except Exception as e:
            print(f"ERROR [FETCH THREAD]: {e}")
            time.sleep(60)

def process_emails_thread():
    """Thread 2: Read unread emails, check if responded, and send AI responses"""
    
    while True:
        try:
            # Load unread emails (smaller list for faster iteration)
            unread_mails = load_json_file(UNREAD_MAIL_FILE)
            
            # Load responded emails
            responded_mails = load_json_file(RESPONDED_MAIL_FILE)
            
            # Create a set of responded message IDs for quick lookup
            responded_ids = {mail.get('message_id') for mail in responded_mails if mail.get('message_id')}
            
            # Process each unread email
            for mail in unread_mails:
                message_id = mail.get('message_id')
                
                # Skip if already responded
                if message_id in responded_ids:
                    continue
                
                # Prepare email content for AI
                email_content = json.dumps({
                    "subject": mail.get('subject'),
                    "from": mail.get('from'),
                    "date": mail.get('date'),
                    "body": mail.get('body')
                }, indent=2)
                
                # Get AI response
                ai_response = email_ai_response(email_content)
                
                # Extract email address from "from" field
                from_field = mail.get('from', '')
                # Simple regex to extract email
                import re
                email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_field)
                to_email = email_match.group(0) if email_match else None
                
                if to_email:
                    # Send email
                    success = send_email(
                        to_email=to_email,
                        subject=mail.get('subject', 'No Subject'),
                        body=ai_response
                    )
                    
                    if success:
                        # Add to responded mails
                        responded_mail_entry = {
                            "message_id": message_id,
                            "original_subject": mail.get('subject'),
                            "original_from": mail.get('from'),
                            "responded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "response": ai_response
                        }
                        
                        responded_mails.append(responded_mail_entry)
                        save_json_file(RESPONDED_MAIL_FILE, responded_mails)
                else:
                    print(f"ERROR: Could not extract email address from: {from_field}")
            
            # Wait before next processing cycle (e.g., 30 seconds)
            time.sleep(30)
            
        except Exception as e:
            print(f"ERROR [PROCESS THREAD]: {e}")
            time.sleep(30)

def flask_server_thread():
    """Thread 3: Run Flask server for API endpoints"""
    
    @app.route('/all', methods=['GET'])
    def get_all_emails():
        """API endpoint to get all emails"""
        try:
            # Get number of emails from query parameter (default: all)
            num_emails = request.args.get('num', default=None, type=int)
            
            # Load all emails
            emails = load_json_file(ALL_MAIL_FILE)
            
            # Limit if num is specified
            if num_emails:
                emails = emails[:num_emails]
            
            return jsonify({
                "success": True,
                "type": "all",
                "count": len(emails),
                "emails": emails
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/unread', methods=['GET'])
    def get_unread_emails():
        """API endpoint to get unread emails"""
        try:
            # Get number of emails from query parameter (default: all)
            num_emails = request.args.get('num', default=None, type=int)
            
            # Load unread emails
            emails = load_json_file(UNREAD_MAIL_FILE)
            
            # Limit if num is specified
            if num_emails:
                emails = emails[:num_emails]
            
            return jsonify({
                "success": True,
                "type": "unread",
                "count": len(emails),
                "emails": emails
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/responded', methods=['GET'])
    def get_responded_emails():
        """API endpoint to get responded emails"""
        try:
            # Get number of emails from query parameter (default: all)
            num_emails = request.args.get('num', default=None, type=int)
            
            # Load responded emails
            emails = load_json_file(RESPONDED_MAIL_FILE)
            
            # Limit if num is specified
            if num_emails:
                emails = emails[:num_emails]
            
            return jsonify({
                "success": True,
                "type": "responded",
                "count": len(emails),
                "emails": emails
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/receive', methods=['GET'])
    def receive_emails():
        """API endpoint to receive emails from JSON files"""
        try:
            # Get type parameter (default: 'unread')
            mail_type = request.args.get('type', default='unread', type=str)
            
            if mail_type == 'all':
                emails = load_json_file(ALL_MAIL_FILE)
            elif mail_type == 'unread':
                emails = load_json_file(UNREAD_MAIL_FILE)
            elif mail_type == 'responded':
                emails = load_json_file(RESPONDED_MAIL_FILE)
            else:
                return jsonify({"error": "Invalid type. Use 'all', 'unread', or 'responded'"}), 400
            
            return jsonify({
                "success": True,
                "type": mail_type,
                "count": len(emails),
                "emails": emails
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/stats', methods=['GET'])
    def get_stats():
        """API endpoint to get email statistics"""
        try:
            all_mails = load_json_file(ALL_MAIL_FILE)
            unread_mails = load_json_file(UNREAD_MAIL_FILE)
            responded_mails = load_json_file(RESPONDED_MAIL_FILE)
            
            return jsonify({
                "success": True,
                "stats": {
                    "total_emails": len(all_mails),
                    "unread_emails": len(unread_mails),
                    "responded_emails": len(responded_mails)
                }
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/', methods=['GET'])
    def home():
        """Home endpoint"""
        return jsonify({
            "message": "MailLLM Server API",
            "status": "running",
            "endpoints": {
                "/all": "GET - Get all emails (query param: ?num=10)",
                "/unread": "GET - Get unread emails (query param: ?num=10)",
                "/responded": "GET - Get responded emails (query param: ?num=10)",
                "/receive": "GET - Receive emails (query param: ?type=unread|all|responded)",
                "/stats": "GET - Get email statistics"
            }
        })
    
    # Run Flask server
    app.run(debug=False, host='0.0.0.0', port=5000, use_reloader=False)

def main():
    """Main function to start both threads"""
    
    if not EMAIL or not PASSWORD:
        print("ERROR: EMAIL and PASSWORD must be set in .env file")
        return
    
    # Create threads
    fetch_thread = threading.Thread(target=fetch_emails_thread, daemon=True)
    process_thread = threading.Thread(target=process_emails_thread, daemon=True)
    flask_thread = threading.Thread(target=flask_server_thread, daemon=True)
    
    # Start threads
    fetch_thread.start()
    process_thread.start()
    flask_thread.start()
    
    print("MailLLM Server Running... (Press Ctrl+C to stop)")
    print("Flask API available at http://localhost:5000")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()
