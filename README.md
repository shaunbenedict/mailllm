# MailLLM Server

**Commit Date:** 23/10/2025, 12:47 AM

## Summary
Flask server with IMAP/SMTP integration for Gmail - receives emails via `/receive` endpoint (returns JSON list) and sends test emails via `/send` endpoint. Uses environment variables for authentication without external APIs.

---

**Update:** 23/10/2025, 1:36 AM

## Summary
Implemented automated email processing system with two-threaded architecture: fetch thread retrieves emails and categorizes them into AllMail.json (all emails) and UnreadMail.json (new emails only), while process thread uses Groq AI to generate contextual responses and automatically replies to unread emails, tracking all responses in RespondedMail.json to prevent duplicates.
