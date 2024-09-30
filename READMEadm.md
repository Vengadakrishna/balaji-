Set up Azure resources:

Ensure you have an active Azure subscription.
Set up Azure Form Recognizer, Azure Blob Storage, and Azure OpenAI services in your Azure portal.


Install required Python packages:
'''
pip install azure-identity azure-ai-formrecognizer azure-storage-blob azure-cognitiveservices-vision-computervision msrest openai python-dotenv

'''
Set up environment variables:
Create a .env file in the same directory as your script and add the following variables:
'''
AZURE_OCR_ENDPOINT=<Your Form Recognizer endpoint>
AZURE_STORAGE_ACCOUNT_URL=<Your Azure Blob Storage account URL>
OPENAI_ENDPOINT=<Your Azure OpenAI endpoint>

'''
Azure AD authentication:

Ensure you're logged in to your Azure account using the Azure CLI:
''' 
az login 

'''

Set the subscription you want to use:
''' 
az account set --subscription <your-subscription-id> 

'''



Update local paths:
Modify the document_directory and csv_file_path variables in the script to point to the correct locations on your local machine.
Run the script:
'''

python your_script_name.py 

'''


Key changes in the updated code:

We're now using DefaultAzureCredential() for authentication, which supports various authentication methods including Azure AD.
The Form Recognizer and Blob Storage clients are initialized using the Azure AD credentials.
The OpenAI client is also initialized using Azure AD credentials.
We've removed the explicit API keys and instead rely on the Azure AD authentication.

This setup allows you to run the script using your Azure ADM account while keeping the OCR and OpenAI services active. The script will process the files from your local directory, but it's authenticated and uses the Azure services through your ADM account.
Remember to grant the necessary permissions to your Azure AD account for accessing these services. You may need to assign roles like "Cognitive Services User" for Form Recognizer and OpenAI, and "Storage Blob Data Contributor" for Blob Storage.
