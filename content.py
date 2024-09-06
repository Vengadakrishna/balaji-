import os
import json
from openai import OpenAI
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv


# load environment variables
load_dotenv()

# setting our OCR and LLM API keys and endpoints
form_recognizer_endpoint = os.getenv("AZURE_OCR_ENDPOINT")
form_recognizer_key = os.getenv("AZURE_OCR_KEY")
document_analysis_client = DocumentAnalysisClient(
    endpoint=form_recognizer_endpoint, credential=AzureKeyCredential(form_recognizer_key)
)

# initialize openAI
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_ENDPOINT")  # Add this line for custom endpoint
)
# initialize fastAPI 
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
        
        chat_completion = client.chat.completions.create(
            messages= [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": messages}
            ],
            model="gpt-3.5-turbo",
            max_tokens=2000
            )
        
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error fetching response from OpenAI: {e}")
        raise

def get_metadata(content):
    prompt= f"""
            You are tasked with extracting specific metadata fields from a document. Your goal is to accurately extract all required fields from the given document text.

            Now, here is the full text of the document:
            
            <document_text>
            {content}
            </document_text>
            

            You will need to extract information for the following fields:
            
            <fields_to_extract>
            Buyer1 First Name
            Buyer1 Middle Name
            Buyer1 Last Name
            Buyer2 First Name
            Buyer2 Middle Name
            Buyer2 Last Name
            Buyer Organization
            Seller1 First Name
            Seller1 Middle Name
            Seller1 Last Name
            Seller2 First Name
            Seller2 Middle Name
            Seller2 Last Name
            Seller Organization
            Lender Name
            Lender - Address
            Lender - Phone Number
            Lender Fax
            Lender Email address
            Lender Marketing Source
            Lender Marketing Rep
            Lender Reference
            Lender Contact 1
            Lender Contact 2
            Listing Agent Name
            Listing Agent Address
            Listing Agent Phone Number
            Listing Agent Fax
            Listing Agent Email address
            Listing Agent Marketing Source
            Listing Agent Marketing Rep
            Listing Agent Reference
            Mortgage Broker Name
            Mortgage Broker Address
            Mortgage Broker Phone Number
            Mortgage Broker Fax
            Mortgage Broker Email address
            Mortgage Broker Marketing Source
            Marketing Rep
            Reference
            Mortgage Broker Contact 1
            Mortgage Broker Contact 2
            APN
            Selling Agent
            Escrow Company Name
            Escrow Company Address
            Escrow Company Phone Number
            Escrow Company Fax
            Escrow Company Email address
            Escrow Company Marketing Source
            Escrow Company Marketing Rep
            Escrow Company Reference
            Escrow Company Contact 1
            Escrow Company Contact 2
            Loan Amount
            Sales Price
            Policy Code
            Transaction Type
            Order Type
            Policy Type
            Product Type
            Property Type
            Rush Order
            Title Officer
            Related order(s):
            Notes
            Instructions
            CPL
            Other
            Payoff Lender
            Title Company Name
            Title Company Lender - Address
            Title Company Lender - Phone Number
            Title Company Fax
            Title Company Email address
            Title Company Marketing Source
            Title Company Marketing Rep
            Title Company Reference
            Settlement Agent Name
            Settlement Agent Lender - Address
            Settlement Agent Lender - Phone Number
            Settlement Agent Fax
            Settlement Agent Email address
            Settlement Agent Marketing Source
            Settlement Agent Marketing Rep
            Settlement Agent Reference
            Escrow Officer
            Title Insurance Premium
            Other (Title Searcher)
            Project Name
            360 Queue
            Settlement Date
            Abstractor
            Underwriter
            Attorney
            Property Use
            Endorsements
            Tax/Map ID
            Government
            HOA
            HOA Management Company
            Qualified Intermediary
            County Taxes
            Lot Number(s)
            Block
            Subdivision/Tract
            Pre-closer/ Escrow Assistant
            Appraiser
            Builder
            General Contractor
            Home Inspector
            Loan Servicer
            Pest Inspector
            Sub Contractor
            Guarantee
            Hazard Insurance Agent
            </fields_to_extract>
            Please follow these instructions to extract the required information:
            1. Carefully read through the entire document text.
            2. For each field listed above, search for relevant information in the document.
            3. Extract the exact text that corresponds to each field.
            4. If a field's information is not found or is unclear, mark it as "Not found" or "Unclear" respectively.
           Guidelines for handling missing or unclear information:
            - If a date is not explicitly stated but can be inferred from context, extract it and note "Inferred" in parentheses after the date.
            - For numeric fields (e.g., loan amounts), extract the full number including cents if available.
            - For names, extract full names as they appear in the document.
            - If a field has multiple relevant entries, include all of them separated by semicolons.
            After extracting all fields, give the response in a field : value."""
    try:
        response = get_openai_response(prompt)
        return response
    except Exception as e:
        print(f"Failed to parse OpenAI response for metadata: {e}")
        return None

def process_document(file_path):    
    try:
        extracted_data = analyze_document(file_path)
        print("OCR is completed, now processing OCR output")
        # print(extracted_data)
        if not extracted_data:
            return {"error": "No data extracted"}
        else:
            processed_data = process_ocr_output(extracted_data)
            print("processed ocr is completed. Now geting values for the fields.")
            # print(processed_data)
        
        fields_and_answers = get_metadata(processed_data)
        max_attempts = 5
        attempt = 0
        
        while fields_and_answers is None and attempt < max_attempts:
            fields_and_answers = get_metadata(processed_data)
            if fields_and_answers is None:
                print(f"Attempt {attempt + 1}: fields is None, retrying...")
            attempt += 1
        return fields_and_answers

    except Exception as e:
        print(f"Document analysis (OCR) failed for the document: {e}")
        return {"error": str(e)}

@app.get("/")
def read_root():
    return {"status": "success"}

@app.post("/process")
def process_route(file_path: str):
    process_result = process_document(file_path)
    return JSONResponse(content=process_result, status_code=200)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
