import pyodbc
import json
import logging
from accounts.accounting.insert_attachments import insert_attachments_data
from accounts.accounting.connection import format_date
from utilities import call_api,parse_datetime

def insert_receipts_data(token,tenant, xero_userid, conn,user_id):
    try:
        cursor = conn.cursor()
        data = call_api(tenant, token,"Receipts")
        try:
            for receipt in data.get("Receipts", []):
                receipt_id = receipt.get("ReceiptID", "")
                date = format_date(receipt.get("Date", ""))
                UpdatedDateUTC = format_date(receipt.get("UpdatedDateUTC", ""))
                contact = json.dumps(receipt.get("Contact", {}))
                user = json.dumps(receipt.get("User", {}))
                sub_total = receipt.get("SubTotal", 0.0)
                total_tax = receipt.get("TotalTax", 0.0)
                total = receipt.get("Total", 0.0)
                has_attachment = receipt.get("HasAttachments", "")
                if has_attachment:
                    insert_attachments_data(token, tenant, xero_userid, conn, "Receipts", receipt_id)

                # Check if the receipt already exists
                cursor.execute("SELECT COUNT(*) FROM Receipts WHERE ReceiptID = ? AND user_id = ?", (receipt_id, user_id))
                result = cursor.fetchone()

                if result[0] == 0:  # If receipt ID doesn't exist in the database
                    cursor.execute("""
                        INSERT INTO Receipts (
                            ReceiptID,  Contact, users, Date,SubTotal, TotalTax, Total,xero_userID,user_id,UpdatedDateUTC
                        ) VALUES (?, ?, ?, ?, ?, ?,?, ?,?,?)
                    """, (receipt_id,  contact, user, date,sub_total, total_tax, total,xero_userid,user_id,UpdatedDateUTC))
                    logging.info(f"Receipts API Receipt with ID {receipt_id} inserted successfully.")
                else:
                    cursor.execute("SELECT UpdatedDateUTC FROM Receipts WHERE ReceiptID = ? AND user_id = ?", (receipt_id, user_id))
                    updated_date_utc_existing = cursor.fetchone()[0]
                    updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                    updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                    created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                    if updated_date_utc_dt == created_date_utc_existing_dt:
                        logging.info(f"Receipt with ID {receipt_id} already exists in the database.")
                    else:
                        cursor.execute("""
                            UPDATE Receipts
                            SET Contact = ?, users = ?, Date = ?, SubTotal = ?, TotalTax = ?, Total = ?, xero_userID = ?, UpdatedDateUTC = ?
                            WHERE ReceiptID = ? AND user_id = ?
                        """, (contact, user, date, sub_total, total_tax, total, xero_userid, UpdatedDateUTC, receipt_id, user_id))
                        logging.info(f"Receipt with ID {receipt_id} updated successfully.")
            conn.commit()
            cursor.close()
            return True
        except pyodbc.Error as e:
            logging.error(f"Receipts API Database error: {e}")
            return False
    except Exception as e:
        logging.error(f"Receipts API Error: {e}")