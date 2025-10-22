import os
import json
from dotenv import load_dotenv
from flask import Flask, jsonify, request

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# JSON file paths
ALL_MAIL_FILE = './logs/AllMail.json'
UNREAD_MAIL_FILE = './logs/UnreadMail.json'
RESPONDED_MAIL_FILE = './logs/RespondedMail.json'

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
        "message": "MailLLM Email API",
        "endpoints": {
            "/all": "GET - Get all emails (query param: ?num=10)",
            "/unread": "GET - Get unread emails (query param: ?num=10)",
            "/responded": "GET - Get responded emails (query param: ?num=10)",
            "/stats": "GET - Get email statistics"
        }
    })

if __name__ == "__main__":
    print("Starting Flask server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
