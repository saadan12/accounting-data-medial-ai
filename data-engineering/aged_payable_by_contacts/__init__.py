import logging
import pyodbc
import json
import azure.functions as func
import os
from dotenv import load_dotenv
load_dotenv()
from accounts.accounting.connection import extract_user_id
from accounts.accounting.connection import get_tenant_id, get_xero_user
from aged_payable_by_contacts.aged_paybale_by_contacts import insert_aged_payables_by_contact_data

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
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
    is_response = insert_aged_payables_by_contact_data(token, tenant, xero_userid, conn, user_id)
    conn.close()
  
    return func.HttpResponse(
            "Success",
            status_code=200
    )
