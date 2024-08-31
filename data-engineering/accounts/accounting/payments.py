import pyodbc
import json
from accounts.accounting.connection import format_date
import logging
from utilities import call_api,parse_datetime
    
def insert_payments_data(token, tenant, xero_userid, conn,user_id):
    try:
        cursor = conn.cursor()
        data = call_api(tenant, token,"Payments")
        try:
            for payment in data.get("Payments", []):
                payment_id = payment.get("PaymentID", "")
                invoice = json.dumps(payment.get("Invoice", {}))
                UpdatedDateUTC = format_date(payment.get("UpdatedDateUTC", ""))
                invoice_number = payment["Invoice"].get("InvoiceNumber", "") if payment.get("Invoice") else ""
                account = json.dumps(payment.get("Account", {}))
                date = format_date(payment.get("Date", ""))
                amount = payment.get("Amount", 0.0)
                payment_type = payment.get("PaymentType", "")
                id = payment_id + str(user_id)
                # Check if the payment already exists
                cursor.execute("SELECT COUNT(*) FROM Payments WHERE PaymentID = ? AND user_id = ?", (payment_id,user_id))
                result = cursor.fetchone()

                if result[0] == 0:  # If payment ID doesn't exist in the database
                    cursor.execute("""
                        INSERT INTO Payments (id,PaymentID, Invoice,Date, InvoiceNumber, Account, Amount, PaymentType,xero_userID,user_id,UpdatedDateUTC)
                        VALUES (?,?, ?, ?, ?, ?, ?,?,?,?,?)
                    """, (id,payment_id, invoice,date, invoice_number, account, amount, payment_type,xero_userid,user_id,UpdatedDateUTC))
                    logging.info(f"Payments API Payment with ID {payment_id} inserted successfully.")
                else:
                    cursor.execute("SELECT UpdatedDateUTC FROM Payments WHERE PaymentID = ? AND user_id = ?", (payment_id, user_id))
                    updated_date_utc_existing = cursor.fetchone()[0]
                    updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                    updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                    created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                    if updated_date_utc_dt == created_date_utc_existing_dt:
                        logging.info(f"Payments API Payment with ID {payment_id} already exists in the database.")
                    else:
                        cursor.execute("""
                            UPDATE Payments
                            SET Invoice = ?, Date = ?, InvoiceNumber = ?, Account = ?, Amount = ?, PaymentType = ?, xero_userID = ?, UpdatedDateUTC = ?
                            WHERE PaymentID = ? AND user_id = ?
                        """, (invoice, date, invoice_number, account, amount, payment_type, xero_userid, UpdatedDateUTC, payment_id, user_id))
                        logging.info(f"Payments API Payment with ID {payment_id} updated successfully.")
            conn.commit()
            cursor.close()
            return True
        except pyodbc.Error as e:
            logging.error(f"Payments API Database error: {e}")
            return False
    except Exception as e:
        logging.error(f"Payments API error: {e}")
