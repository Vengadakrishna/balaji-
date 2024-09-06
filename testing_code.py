from dotenv import load_dotenv
from openai import OpenAI
import os

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    # base_url=os.environ.get("OPENAI_ENDPOINT")  # Comment this line out
)

def test_openai_connection():
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, are you working?"}
            ]
        )
        print("API Connection Successful!")
        print("Response:", response.choices[0].message.content)
        return True
    except Exception as e:
        print("API Connection Failed:")
        print(str(e))
        return False

# Call the test function
if __name__ == '__main__':
    test_openai_connection()