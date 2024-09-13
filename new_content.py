import os
import json
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
import requests
from openai import AzureOpenAI


# Load environment variables
load_dotenv()

# Set up API keys and endpoints
form_recognizer_endpoint = os.getenv("AZURE_OCR_ENDPOINT")
form_recognizer_key = os.getenv("AZURE_OCR_KEY")
document_analysis_client = DocumentAnalysisClient(
    endpoint=form_recognizer_endpoint, credential=AzureKeyCredential(form_recognizer_key)
)



# Initialize FastAPI
app = FastAPI()

def analyze_document(document_path):
    try:
        with open(document_path, "rb") as f:
            poller = document_analysis_client.begin_analyze_document(
                "prebuilt-document", document=f.read()
            )
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
            messages = f"You are a helpful assistant that fixes errors in OCR outputs and provides correct data in the same JSON format.:\n{page_content}"
            response = get_openai_response(messages)
            corrected_output_parts.append({list(page.keys())[0]: response})
        
        return corrected_output_parts
    except json.JSONDecodeError as e:
        print(f"Error parsing corrected JSON: {e}") 
        raise



def get_openai_response(messages):
    try:
        client = AzureOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            api_version="2024-07-01-preview",  
            azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
            azure_deployment="aipal",
        )
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  
            messages=[
                {"role": "user", "content": "You are a helpful assistant."},
                {"role": "user", "content": messages}
            ],
            max_tokens=800
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error fetching response from Azure OpenAI: {e}")
        return None

    
def get_metadata(content):
   prompt = """
You are an AI assistant tasked with extracting specific metadata fields from a document. Your goal is to accurately extract all required fields from the given document text and provide confidence scores for each extraction. Follow these instructions carefully:

1. Here is the full text of the document:
<document_text>
{content}
</document_text>

2. You need to extract information for the following fields:

<fields_to_extract>
Seller Name
Seller Suffix
Seller Relationship
Seller Current Address
Seller Same as Property address
Seller City
Seller State
Seller Zip Code
Seller Email address
Seller WorkPhone /Ext:
Seller Fax
Seller Marketing Rep
Seller Marketing Source
Buyer Name
Buyer Suffix
Buyer Relationship
Buyer Current Address
Buyer Same as Property address
Buyer City
Buyer State
Buyer Zip Code
Buyer Email address
Buyer WorkPhone /Ext:
Buyer Fax
Buyer Marketing Rep
Buyer Marketing Source

</fields_to_extract>

3. To extract the information:
a. Carefully read through the entire document text.
b. For each field listed, search for relevant information within the document.
c. Pay attention to headers, labels, or sections that might indicate where specific information is located.
d. Be precise in your extraction, ensuring you capture the exact information as it appears in the document.

4. Format your output as follows:
a. Begin your response with <extracted_metadata> and end the response with </extracted_metadata>.
b. For each extracted field, use the following format:
[
'Field'-the name of the feild : 'Extracted Value' - extracted value,
'Confidence score': [0-100]
]
c. Provide a confidence score (0-100) for each extracted field, where 0 means no confidence and 100 means absolute certainty.
d. If a field has multiple values (e.g., multiple buyer names), include all values separated by commas within the same field tag.

5. If you cannot find information for a particular field:
a. If the information is clearly not present in the document, use:
[
'Field': Not provided,
'Confidence': 100
]
b. If the information is ambiguous or unclear, use:
[
'Field': Unclear - [brief explanation],
'Confidence': [appropriate low score]
]

6. Before finalizing your response:
a. Double-check each extracted field against the original document to ensure accuracy.
b. Verify that you have addressed all fields listed in the <fields_to_extract> section.

Remember, accuracy and completeness are crucial. Take your time to carefully extract all required information from the document and provide appropriate confidence scores for each extraction.
   """
   try:
       response = get_openai_response(prompt.format(content=content))
       return response
       # Parse the XML-like response
    #    import xml.etree.ElementTree as ET
    #    root = ET.fromstring(response)
    #    return {elem.tag: elem.text for elem in root}
        
   except Exception as e:
       print(f"Failed to parse OpenAI response for metadata: {e}")
       return None

def process_document(file_path):
    try:
        extracted_data = analyze_document(file_path)
        print("OCR is completed, now processing OCR output")
        if not extracted_data:
            return {"error": "No data extracted"}
        else:
            processed_data = process_ocr_output(extracted_data)
            print("Processed OCR is completed. Now getting values for the fields.")

        fields_and_answers = get_metadata(processed_data)
        max_attempts = 5
        attempt = 0

        while fields_and_answers is None and attempt < max_attempts:
            fields_and_answers = get_metadata(processed_data)
            if fields_and_answers is None:
                print(f"Attempt {attempt + 1}: Unexpected response from OpenAI, retrying...")
            attempt += 1

        if fields_and_answers is None:
            return {"error": "Failed to extract metadata from OpenAI"}
        else:
            return fields_and_answers

    except Exception as e:
        print(f"Document analysis (OCR) failed for the document: {e}")
        return {"error": str(e)}
    

@app.get("/")
def read_root():
    return {"status": "success"}

@app.get("/process")
def process_route(file_path: str):
    process_result = process_document(file_path)
    return JSONResponse(content=process_result, status_code=200)

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
