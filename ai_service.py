from groq import Groq # type: ignore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Groq API key from .env file
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

client = Groq(api_key=GROQ_API_KEY)

def email_ai_response(email_content):
     chat_completion = client.chat.completions.create(
         messages=[
             # Set an optional system message. This sets the behavior of the
             # assistant and can be used to provide specific instructions for
             # how it should behave throughout the conversation.
             {
                 "role": "system",
                 "content": "You're MailLLM. An AI service which answers questions of people through email. youre supposed to respond with the answer to the question asked to you. Respond with just the string with the answer for the question in a proper email format. with Dear <user's name.. just the first name>... and Best Regards, Mail LLM.. Maybe add the text after salutation with something like 'From your prior request,' or 'From your mail request with the question,'. Donot add text like 'Subject: Re:' and symbol '>' before the email body."
             },
             # Set a user message for the assistant to respond to.
             {
                 "role": "user",
                 "content": email_content,
             }
         ],

         # The language model which will generate the completion.
         model="llama-3.1-8b-instant"
     )

     # Return the completion returned by the LLM.
     return chat_completion.choices[0].message.content