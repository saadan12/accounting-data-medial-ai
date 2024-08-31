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
from accounts.accounting.payments import insert_payments_data
from accounts.accounting.purchase_order import insert_purchase_orders_data
from accounts.accounting.receipts import insert_receipts_data
from accounts.accounting.accounts import get_account_data
from accounts.accounting.employee import get_employee_data
from accounts.accounting.contacts import get_contact_data
from accounts.accounting.bank_transaction import get_bank_transaction_data
from accounts.accounting.creadit_notes import get_credit_note_data
from accounts.accounting.expense_claims import get_expense_claim_data
from accounts.accounting.items import insert_items_data
from accounts.accounting.invoice import insert_invoices_data
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

        is_response = get_account_data(token,tenant, xero_userid, conn,user_id)
        is_response = insert_payments_data(token, tenant, xero_userid, conn,user_id)
        is_response = get_bank_transaction_data(token,tenant, xero_userid, conn,user_id)
        is_response = insert_invoices_data(token, tenant, xero_userid, conn,user_id)
        is_response = get_credit_note_data(token,tenant, xero_userid, conn,user_id)
        is_response = get_expense_claim_data(token, tenant, xero_userid, conn,user_id)
        is_response = get_employee_data(token,tenant, xero_userid, conn,user_id)
        is_response = get_contact_data(token,tenant, xero_userid, conn,user_id)
        is_response = insert_items_data(token, tenant, xero_userid, conn,user_id)
        is_response = insert_purchase_orders_data(token, tenant, xero_userid, conn,user_id)
        is_response = insert_receipts_data(token, tenant, xero_userid, conn,user_id)
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