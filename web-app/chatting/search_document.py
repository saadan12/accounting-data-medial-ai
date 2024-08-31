from pypdf import PdfReader
from datetime import datetime,timezone
from docx import Document
from uuid import uuid4
import logging
import openai
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
 
import os
import dotenv
dotenv.load_dotenv()
 
openai.api_type = str(os.environ["OPENAI_API_TYPE"])
openai.api_key = str(os.environ["OPENAI_API_KEY"])
openai.api_base = str(os.environ["OPENAI_API_BASE"])
openai.api_version = str(os.environ["OPENAI_API_VERSION"])
endpoint = os.environ.get("SEARCH_ENDPOINT")
index_name = "document_chat"
key = os.environ.get("SEARCH_KEY")
 
def read_docx(file_path):
    document = Document(file_path)
    return [paragraph.text for paragraph in document.paragraphs]
 
def read_pdf(file_obj):
    reader = PdfReader(file_obj)
    return [page.extract_text() for page in reader.pages]
 
def convert_file_to_text(pdf_file_path,user_id, only_text=False):
    page_list = []
    file_extension = os.path.splitext(pdf_file_path.name)[1].lower()
    if file_extension == '.docx':
        page_list = read_docx(pdf_file_path)
    elif file_extension == '.pdf':
        page_list = read_pdf(pdf_file_path)
    if only_text:
        return ' '.join(page_list)
    current_time = datetime.now(timezone.utc).isoformat()  # Get current time in ISO format
    # pdf_file_path.split("/")[-1]
    all_pages_text = [{
         "ID": f"{uuid4()}", "user_id": str(user_id), "file_name" : pdf_file_path.name,
        "text": page # Add current timestamp
    } for idx, page in enumerate(page_list)]
    print("all_pages_text ",all_pages_text)
    return all_pages_text
 
def get_search_connection():
    credential = AzureKeyCredential(key)
    client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)
    return client
 
def save_embedding_to_search(documents):
    #Todo convert 'text' into vector and create a new field text_vector in index
    client = get_search_connection()
    client.upload_documents(documents=documents)
    client.close()
 
def save_file_to_search(filename, user_id):
    documents = convert_file_to_text(filename, user_id)
    save_embedding_to_search(documents)
 
def search_documents(query, user_id):
    #Todo convert query into vector and do vector search instead of vector search
    client = get_search_connection()
    results = client.search(query, filter=f"user_id eq '{user_id}' ")
    filtered_results = []
    for result in results:
        filtered_result = {}
        filtered_result["text"] = result.get("text")
        filtered_results.append(filtered_result)
    client.close()
    return filtered_results[:20]
 
def call_large_model(messages, user_id):
    example_query_results = search_documents(messages,user_id)
    print("AI result: ", example_query_results)
    message = [{"role": "user", "content": f"{messages} in {example_query_results}"}]
    response = openai.chat.completions.create(
                messages=message,
                model="gpt-4o",
                max_tokens=100,
                temperature=0.4,
                top_p=0.9
            )
    print(f"Final Result:{response.choices[0].message.content}")
    return response.choices[0].message.content
 