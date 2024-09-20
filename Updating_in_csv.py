import os
import json
import csv
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv
from openai import AzureOpenAI


load_dotenv()

#  API keys and endpoints
form_recognizer_endpoint = os.getenv("AZURE_OCR_ENDPOINT")
form_recognizer_key = os.getenv("AZURE_OCR_KEY")
document_analysis_client = DocumentAnalysisClient(
    endpoint=form_recognizer_endpoint, credential=AzureKeyCredential(form_recognizer_key)
)


# directory where documents are stored
document_directory = r"D:/testingoffice/testingDocumentType"
csv_file_path = r"D:/testingoffice/metadata.csv"



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
            messages = f"Correct the following OCR text:\n{page_content}"
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
                {"role": "user", "content": messages}
            ],
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error fetching response from OpenAI: {e}")
        return None

def get_metadata(content):
    prompt = f"""
    You are an AI assistant tasked with extracting specific metadata fields from a document. Your goal is to accurately extract all required fields from the given document text. Follow these instructions carefully:
    1. Here is the full text of the document:
    <document_text>
    {content}
    </document_text>
    2. You need to extract information for the following fields:
    <fields_to_extract>
    Seller Name, Seller Suffix, Seller Relationship, Seller Current Address, Seller Same as Property address, Seller City, Seller State, Seller Zip Code, Seller Email address, Seller WorkPhone /Ext:, Seller Fax, Seller Marketing Rep, Seller Marketing Source, Buyer Name, Buyer Suffix, Buyer Relationship, Buyer Current Address, Buyer Same as Property address, Buyer City, Buyer State, Buyer Zip Code, Buyer Email address, Buyer WorkPhone /Ext:, Buyer Fax, Buyer Marketing Rep, Buyer Marketing Source
    </fields_to_extract>
    3. To extract the information:
    a. Carefully read through the entire document text.
    b. For each field listed, search for relevant information within the document.
    c. Pay attention to headers, labels, or sections that might indicate where specific information is located.
    d. Be precise in your extraction, ensuring you capture the exact information as it appears in the document.
    4. Format your output as follows:
    a. Return the metadata fields and values as a JSON object.
    b. The keys should be the field names and the values should be the extracted data.
    c. If the field is not found, return it with a value "Not provided".
    d. The JSON object should be human-readable, with field names as keys and their corresponding extracted values as values.
    """
    try:
        response = get_openai_response(prompt)
        if response is None:
            print("OpenAI API returned None. Check API key and quota.")
            return None

        print("OpenAI response:")
        print(response)

        # Parse the response as JSON
        metadata = json.loads(response)
        return metadata
    except Exception as e:
        print(f"Failed to parse OpenAI response: {e}")
        return None

def process_document(file_path):
    try:
        print(f"Starting document analysis for file: {file_path}")
        extracted_data = analyze_document(file_path)
        if not extracted_data:
            print("No data extracted from OCR")
            return {"error": "No data extracted"}

        processed_data = process_ocr_output(extracted_data)
        fields_and_answers = get_metadata(processed_data)

        if fields_and_answers is None:
            return {"error": "Failed to extract metadata from OpenAI"}
        else:
            return fields_and_answers
    except Exception as e:
        print(f"Error in process_document: {str(e)}")
        return {"error": str(e)}
    
def ensure_directory_exists(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)

def update_csv(fields_and_answers, csv_file_path, office_name, document_type, filename):
    try:
        # Ensure the directory exists
        ensure_directory_exists(os.path.dirname(csv_file_path))

        # Define the new fields we want to add
        new_fields = ['office name', 'document type', 'filename']

        # Combine all fields
        all_fields = new_fields + [field for field in fields_and_answers.keys() if field not in new_fields]

        # Prepare the row data
        row_data = {
            'office name': office_name,
            'document type': document_type,
            'filename': filename
        }
        row_data.update(fields_and_answers)

        # Check if the file exists and read its current content
        file_exists = os.path.exists(csv_file_path)
        existing_data = []
        if file_exists:
            with open(csv_file_path, 'r', newline='') as f:
                reader = csv.DictReader(f)
                existing_data = list(reader)
                existing_fields = reader.fieldnames

            # Update all_fields to include any missing existing fields
            for field in existing_fields:
                if field not in all_fields:
                    all_fields.append(field)

        # Write to CSV
        with open(csv_file_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_fields)
            writer.writeheader()
            for row in existing_data:
                writer.writerow(row)
            writer.writerow(row_data)

        print(f"Successfully updated CSV for file: {filename}")

    except Exception as e:
        print(f"Error while updating CSV: {e}")


def process_all_documents(directory_path):
    for root, dirs, files in os.walk(directory_path):
        for file_name in files:
            if file_name.endswith((".pdf", ".jpg", ".jpeg", ".png")):  # Add extensions as needed
                file_path = os.path.join(root, file_name)
                
                office_name = "bangalore"  # here we should mention the 'office name' 
                document_type = 'DEED'  # here 'document type' 

                print(f"Processing file: {file_name} (Office: {office_name}, Document Type: {document_type})")
                
                
                result = process_document(file_path)
                if "error" not in result:
                    update_csv(result, csv_file_path, office_name, document_type, file_name)


def main():
    # Process all documents in the directory
    print("Processing documents in directory...")
    process_all_documents(document_directory)
    
if __name__ == "__main__":
    main()
