import logging
import azure.functions as func
import pyodbc
import json
from azure.identity import ClientSecretCredential
from azure.keyvault.secrets import SecretClient
import os
from dotenv import load_dotenv
load_dotenv()

from accounts.accounting.connection import get_tenant_id, get_xero_user

from accounts.accounting.journals import insert_journals_data
from accounts.accounting.budget import insert_budgets_data
from accounts.accounting.quotes import insert_quotes_data
from accounts.accounting.connection import extract_user_id

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        req_body = req.get_json()
        logging.info(f"Input: {req_body}")
        secret_name = req_body['secret_name']
        secret_value = req_body['secret_value']
        user_id = extract_user_id(secret_name)
        secret_value_dict = json.loads(secret_value)
        logging.info("secret_value_dict %s", secret_value_dict)
        token = secret_value_dict['access_token']
        logging.info("token %s", token) 
        
        db_driver = os.getenv('DB_DRIVER')
        db_server = os.getenv('DB_SERVER')
        db_port = os.getenv('DB_PORT')
        db_name = os.getenv('DB_NAME')
        db_uid = os.getenv('DB_UID')
        db_pwd = os.getenv('DB_PWD')
        db_encrypt = os.getenv('DB_ENCRYPT')
        db_trust_server_certificate = os.getenv('DB_TRUST_SERVER_CERTIFICATE')
        db_connection_timeout = os.getenv('DB_CONNECTION_TIMEOUT')


        tenant = get_tenant_id(token)
        xero_userid = get_xero_user(token)
        conn = pyodbc.connect(
                f"Driver={{{db_driver}}};"
                f"Server=tcp:{db_server},{db_port};"
                f"Database={db_name};"
                f"Uid={db_uid};"
                f"Pwd={db_pwd};"
                f"Encrypt={db_encrypt};"
                f"TrustServerCertificate={db_trust_server_certificate};"
                f"Connection Timeout={db_connection_timeout};"
                )
        logging.info("DB Connection Successful")
        logging.info("Start Exceution")

        
        is_response = insert_journals_data(token, tenant, xero_userid, conn,user_id)
        is_response = insert_budgets_data(token, tenant, xero_userid, conn,user_id)
        is_response = insert_quotes_data(token, tenant, xero_userid, conn,user_id)
        if is_response:
            print("Successfull")
        else:
            print("Failure")
        conn.close()
    except Exception as e:
        logging.error(f"Data Fetching Error {e}")  
        
    return func.HttpResponse(
        f"This HTTP triggered function executed successfully. Data:",
        status_code=200
    )