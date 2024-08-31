import openai
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import SearchIndex
from dotenv import load_dotenv
load_dotenv()
import os
import openai
import pyodbc
import logging
from datetime import datetime

DB_HOST=os.environ["DB_HOST"]
DB_NAME=os.environ["DB_NAME"]
DB_PASSWORD=os.environ["DB_PASSWORD"]
DB_USER=os.environ["DB_USER"]
openai.api_type = str(os.environ["OPENAI_API_TYPE"])
openai.api_key = str(os.environ["OPENAI_API_KEY"])
openai.api_base = str(os.environ["OPENAI_API_BASE"])
openai.api_version = str(os.environ["OPENAI_API_VERSION"])
search_endpoint = os.environ.get("SEARCH_ENDPOINT")
search_key = os.environ.get("SEARCH_KEY")

def get_conn():
    conn = pyodbc.connect(
    )
    cursor = conn.cursor()
    return conn, cursor

def close_conn(conn, cursor):
    cursor.close()
    conn.close()

def get_data_by_query(query):
    conn, cursor = get_conn()
    cursor.execute(query)
    # convert the data into a list of dictionaries
    results = [dict(zip([column[0] for column in cursor.description], row)) for row in cursor.fetchall()]
    close_conn(conn, cursor)
    return results
def save_logs_query(question,sql_query,answer,user_id):
    conn, cursor = get_conn()
    cursor.execute("INSERT INTO Logs (question, sql_query, answer, user_id, query_time) VALUES (?, ?, ?, ?, ?)",(question,str(sql_query),str(answer),int(user_id),datetime.now()))
    conn.commit() 
    cursor.close()
    return f"Logs saved with these values: {question}"

def get_search_connection(index):
    credential = AzureKeyCredential(search_key)
    client = SearchClient(endpoint=search_endpoint, index_name=index, credential=credential)
    return client

def save_embedding_to_search(documents, index):
    client = get_search_connection(index)
    client.upload_documents(documents=documents)
    client.close()

def merge_or_upload_documents(documents, index):
    client = get_search_connection('sql_query')
    client.merge_or_upload_documents(documents=documents)
    client.close()

def create_index(index_name, fields):
    credential = AzureKeyCredential(search_key)
    client = SearchIndexClient(endpoint=search_endpoint, credential=credential)
    index = SearchIndex(
        name=index_name,
        fields=fields
    )
    client.create_index(index)
    client.close()

def search_example_documents(search_text):
    client = get_search_connection('sql_query')
    results = client.search(search_text)
    filtered_results = []
    for result in results:
        filtered_results.append({
            "query": result.get("query"),
            "sql": result.get("sql"),
            "schema": result.get("schema"),
        })
    client.close()
    return filtered_results[:2]

def request_to_model(input, user_id):
    prompt = input
    my_context = ['']
    instructions=f"""
        add include user_id if it exists in schema otherwise exclude: {user_id} in query like AND user_id={user_id}
       Important: remove these from query : ```sql
        ```
        """
    example_query_results= search_example_documents(prompt)
    logging.info(f"Search Results: {example_query_results}")
    try:
        check_hint = example_query_results[0]['query'].split('Hint::')[1]
    except:
        check_hint=''
    try:
        chat_history = [{"role":"user","content":example_query_results[0]['query']},
                        {"role":"assistant","content":example_query_results[0]['sql']},
            {"role": "user", "content": f"Give me only sql query (not any single more character except query)\n {prompt}::Hint::{check_hint} \n schema: {example_query_results[0]['schema']} \n {instructions}\n context {my_context}"}]
        response = openai.chat.completions.create(
            messages=chat_history,
            model="gpt-4o",
            max_tokens=1000,
            temperature=0.4,
            top_p=0.9
        )
        response=response.choices[0].message.content
        logging.info(f"Query Generation: {response}")
        try:
            output = get_data_by_query(response)
        except Exception as e:
            output=e
        save_logs_query(prompt,response,output,user_id)
        logging.info(f"Query output:",output)
        instructions=os.environ['INSTRUCTIONS']
        chat_history = [{"role": "user", "content": f"Give me answer only related to question and include importanrt facts and values: prompt: {prompt} \n\ {output} \n \n {instructions}"}]
        response = openai.chat.completions.create(
            messages=chat_history,
            model="gpt-4o",
            max_tokens=1000,
            temperature=0.4,
            top_p=0.9
        )
        logging.info(f"Final Result:{response.choices[0].message.content}")
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"Final Output Error: {e}")
        return f"Try with another question {e}"
# import uuid
# documents=[
#     {
#       "ID": str(uuid.uuid4()),
#       "query": "Calculate the total Year-to-Date Credit (YTD_Credit) for June 2024?",
#       "sql": "SELECT SUM(YTD_Credit) AS TotalYTDCredit_June2024 FROM TrialBalance WHERE YEAR(ReportDate) = 2024 AND MONTH(ReportDate) = 6;",
#        "schema":"[TrialBalance] ([Debit] FLOAT (53) NULL, [Credit] FLOAT (53) NULL, [YTD_Debit] FLOAT (53) NULL, [YTD_Credit] FLOAT (53) NULL, [Account_ID] NVARCHAR (255) NULL, [user_id] INT NULL, [ReportDate] DATE NULL, [UpdatedDateUTC] DATETIME NULL);"
#     }]
# merge_or_upload_documents(documents,'sql_query')