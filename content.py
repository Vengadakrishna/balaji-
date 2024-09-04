import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

content = "the content is this"

def get_openai_response(messages):
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="gpt-3.5-turbo",
            max_tokens=2000
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error fetching response from OpenAI: {e}")
        raise

def get_metadata(content, fields):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that extracts specific information from document content."},
        {"role": "user", "content": f"Extract the following information from this content, filling in the values for each field:\n{content}\n\nFields: {fields}"}
    ]
    try:
        response = get_openai_response(messages)
        return response
    except Exception as e:
        print(f"Failed to parse OpenAI response for metadata: {e}")
        return None

def get_data_for_the_fields():
    fields = {
        "document type": "",
        "what is the document or content about": ""
    }
    return get_metadata(content, fields)

output = get_data_for_the_fields()
print(output)