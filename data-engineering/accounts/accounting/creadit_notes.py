import requests
import pyodbc
import json
import logging
from accounts.accounting.insert_attachments import insert_attachments_data
from accounts.accounting.connection import format_date
from utilities import call_api,parse_datetime

def get_credit_note_data(token, tenant, xero_userid, conn,user_id):
    # try:
        cursor = conn.cursor()
        page = 1
        while True:
            data = call_api(tenant, token,f"CreditNotes?page={page}")
            page+=1
            length_of_data = len(data.get("CreditNotes", []))
            if length_of_data == 0:
                break
            try:
                for credit_note in data.get("CreditNotes", []):
                    first_line_item = credit_note.get("LineItems", [])
                    if first_line_item:
                        description = first_line_item[0].get("Description", "")
                        quantity = first_line_item[0].get("Quantity", 0.0)
                        unit_amount = first_line_item[0].get("UnitAmount", 0.0)
                    else:
                        description = ""
                        quantity = 0.0
                        unit_amount = 0.0
                    credit_note_id = credit_note.get("CreditNoteID", "")
                    UpdatedDateUTC = format_date(credit_note.get("UpdatedDateUTC", ""))
                    type_ = credit_note.get("Type", "")
                    LineItems = json.dumps(credit_note.get("LineItems", []))
                    CreditNoteNumber = credit_note.get("CreditNoteNumber", "")
                    contactName = credit_note.get("Contact", {}).get("Name", "")
                    date = format_date(credit_note.get("Date", ""))
                    due_date = format_date(credit_note.get("FullyPaidOnDate", ""))
                    status = credit_note.get("Status", "")
                    sub_total = credit_note.get("SubTotal", 0.0)
                    total_tax = credit_note.get("TotalTax", 0.0)
                    total = credit_note.get("Total", 0.0)
                    id = credit_note_id + str(user_id)
                    has_attachment = credit_note.get("HasAttachments", "")
                    if has_attachment:
                        insert_attachments_data(token, tenant, xero_userid, conn, "CreditNotes", credit_note_id)
                    cursor.execute("SELECT COUNT(*) FROM CreditNotes WHERE CreditNoteID = ? AND user_id = ? ", (credit_note_id,user_id))
                    result = cursor.fetchone()

                    if result[0] == 0:  # If credit note ID doesn't exist in the database
                        cursor.execute("""

                            INSERT INTO CreditNotes (id,CreditNoteID, Type,DueDate, ContactName, Status, SubTotal, TotalTax, Total, xero_userID,user_id,date,CreditNoteNumber,LineItems,UpdatedDateUTC, Description,Quantity,UnitAmount)
                            VALUES (?,?, ?, ?, ?, ?, ?,?, ?,?,?,?,?,?,?,?,?,?)
                        """, (id,credit_note_id, type_,due_date, contactName, status, sub_total, total_tax, total,xero_userid,user_id,date,CreditNoteNumber,LineItems,UpdatedDateUTC,description, quantity,unit_amount))
                        logging.info(f"Credit Notes API Credit note with ID {credit_note_id} inserted successfully.")
                    else:
                        cursor.execute("SELECT UpdatedDateUTC FROM CreditNotes WHERE CreditNoteID = ? AND user_id = ?", (credit_note_id, user_id))
                        updated_date_utc_existing = cursor.fetchone()[0]
                        updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                        updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                        created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                        if updated_date_utc_dt == created_date_utc_existing_dt:
                            logging.info(f"Credit Notes API Credit note with ID {credit_note_id} already exists in the database.")
                        else:
                            cursor.execute("""
                                UPDATE CreditNotes
                                SET Description = ?,Quantity = ?,UnitAmount = ?, Type = ?, DueDate = ?, ContactName = ?, Status = ?, SubTotal = ?, TotalTax = ?, Total = ?, xero_userID = ?, date = ?, CreditNoteNumber = ?, LineItems = ?, UpdatedDateUTC = ?
                                WHERE CreditNoteID = ? AND user_id = ?
                            """, (description, quantity,unit_amount, type_, due_date, contactName, status, sub_total, total_tax, total, xero_userid, date, CreditNoteNumber, LineItems, UpdatedDateUTC, credit_note_id, user_id))
                            logging.info(f"Credit Notes API Credit note with ID {credit_note_id} updated successfully.")
                conn.commit()
            except pyodbc.Error as e:
                logging.error(f"Credit Notes API Database error: {e}")
                return False
        cursor.close()
        return True
        # except Exception as e:
    #     logging.error(f"Credit Notes API error: {e}")