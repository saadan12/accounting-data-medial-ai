import requests
import pyodbc
import json
from accounts.accounting.connection import format_date
from accounts.accounting.insert_attachments import insert_attachments_data
import logging
import datetime
from utilities import call_api,parse_datetime

    
def get_bank_transaction_data(token, tenant, xero_userID, conn,user_id):
    try:
        cursor = conn.cursor()
        data = call_api(tenant, token,"BankTransactions")
        try:
            for transaction in data.get("BankTransactions", []):
                bank_transaction_id = transaction.get("BankTransactionID", "")
                UpdatedDateUTC = format_date(transaction.get("UpdatedDateUTC", ""))
                type = transaction.get("Type", "")
                ContactName = transaction.get("Contact", {}).get("Name", "")
                bank_account = json.dumps(transaction.get("BankAccount", {}))
                date = format_date(transaction.get("Date", ""))
                reference = transaction.get("Reference", "")
                sub_total = transaction.get("SubTotal", 0.0)
                total_tax = transaction.get("TotalTax", 0.0)
                total = transaction.get("Total", 0.0)
                has_attachment = transaction.get("HasAttachments", "")
                id = bank_transaction_id+str(user_id)
                if has_attachment:
                    insert_attachments_data(token, tenant, xero_userID, conn, "BankTransactions", bank_transaction_id)
                
                # Check if the bank transaction already exists
                cursor.execute("SELECT COUNT(*) FROM BankTransactions WHERE bank_transaction_id = ? AND user_id = ? ", (bank_transaction_id,user_id))
                result = cursor.fetchone()
                
                if result[0] == 0:  # If bank transaction ID doesn't exist in the database
                    cursor.execute("""
                        INSERT INTO BankTransactions (id,type, ContactName,date, bank_account, reference, sub_total, total_tax, total, bank_transaction_id, xero_userID,user_id,UpdatedDateUTC)
                        VALUES (?,?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
                    """, (id,type, ContactName,date, bank_account, reference, sub_total, total_tax, total, bank_transaction_id, xero_userID,user_id,UpdatedDateUTC))
                    logging.info(f"Bank Transactions API Bank transaction with ID {bank_transaction_id} inserted successfully.")
                else:
                    cursor.execute("SELECT UpdatedDateUTC FROM BankTransactions WHERE bank_transaction_id = ? AND user_id =?", (bank_transaction_id, user_id))

                    updated_date_utc_existing = cursor.fetchone()[0]
                    updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                    updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                    created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                    if updated_date_utc_dt == created_date_utc_existing_dt:
                        logging.info(f"Bank Transactions API Bank transaction with ID {bank_transaction_id} already exists in the database.")
                    else:
                        cursor.execute("""
                            UPDATE BankTransactions
                            SET type = ?, ContactName = ?, date = ?, bank_account = ?, reference = ?,
                                sub_total = ?, total_tax = ?, total = ?, xero_userID = ?, UpdatedDateUTC = ?
                            WHERE bank_transaction_id = ? AND user_id = ?
                        """, (type, ContactName, date, bank_account, reference, sub_total,
                            total_tax, total, xero_userID, UpdatedDateUTC, bank_transaction_id, user_id))
                        logging.info(f"Bank Transactions API Bank transaction with ID {bank_transaction_id} updated successfully.")
            conn.commit()
            cursor.close()
            return True
        except pyodbc.Error as e:
            logging.error(f"Bank Transactions API Database error: {e}")
            return False
    except Exception as e:
        logging.error(f"Bank Transactions API Error : {e}")
