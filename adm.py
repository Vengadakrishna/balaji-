import os
import json
import csv
from azure.identity import DefaultAzureCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# azure ADM credentials
credential = DefaultAzureCredential()

# form recognizer setup
form_recognizer_endpoint = os.getenv("AZURE_OCR_ENDPOINT")
document_analysis_client = DocumentAnalysisClient(endpoint=form_recognizer_endpoint, credential=credential)

# azure blob storage setup
storage_account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
blob_service_client = BlobServiceClient(account_url=storage_account_url, credential=credential)

# openAI setup
openai_client = AzureOpenAI(
    api_version="2024-07-01-preview",
    azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
    azure_deployment="aipal",
    credential=credential
)

# Local directory where documents are stored
document_directory = r"D:/testingoffice/testingDocumentType"
csv_file_path = r"D:/testingoffice/metadata.csv"

def analyze_document(document_path):
    try:
        with open(document_path, "rb") as f:
            poller = document_analysis_client.begin_analyze_document("prebuilt-document", document=f.read())
        result = poller.result()

        extracted_data = []
        for page in result.pages:
            page_content = " ".join([line.content for line in page.lines])
            extracted_data.append({str(page.page_number - 1): page_content})
        return extracted_data
    except Exception as e:
        print(f"Error during document analysis: {e}")
        raise

def process_ocr_output(ocr_output):
    try:
        corrected_output_parts = []

        for page in ocr_output:
            page_content = list(page.values())[0]
            messages = f"Correct the following OCR text:\n{page_content}"
            response = get_openai_response(messages)
            corrected_output_parts.append({list(page.keys())[0]: response})

        return corrected_output_parts
    except json.JSONDecodeError as e:
        print(f"Error parsing corrected JSON: {e}")
        raise

def get_openai_response(messages):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": messages}
            ],
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error fetching response from OpenAI: {e}")
        return None



if __name__ == "__main__":
    main()
