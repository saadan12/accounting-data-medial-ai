import logging
import azure.functions as func
import pyodbc
import ast
import json
import os
from dotenv import load_dotenv
load_dotenv()
from reports.reports.connection import extract_user_id
from reports.reports.connection import get_tenant_id, get_xero_user
from reports.reports.profit_loss import insert_profit_and_loss_data
from reports.reports.balance_sheet import insert_balance_sheet_data
from reports.reports.trial_balance import insert_trial_balance_data
from reports.reports.budget_summary import get_budget_summary_data


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
        token = secret_value_dict["access_token"]
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
        is_response = insert_profit_and_loss_data(token, tenant, conn, user_id)
        is_response = insert_balance_sheet_data(token, tenant, xero_userid, conn, user_id)
        is_response = insert_trial_balance_data(token, tenant, conn, user_id)
        is_response = get_budget_summary_data(token, tenant, xero_userid, conn, user_id)
        
        conn.close()

        return func.HttpResponse(
            "Success",
            status_code=200
        )
    except Exception as e:
        logging.error(f"Reports Init Error: {e}")
        return func.HttpResponse(f"Invalid input: {e}", status_code=200)
    
