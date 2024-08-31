import pyodbc
import logging
from accounts.accounting.insert_attachments import insert_attachments_data
from accounts.accounting.connection import format_date
from utilities import call_api,parse_datetime

def insert_invoices_data(token, tenant,xero_userid, conn,user_id):
    try:
        cursor = conn.cursor()
        page = 1
        while True:
            data = call_api(tenant, token,f"Invoices?page={page}")
            length_of_data = len(data.get("Invoices", []))
            page+=1
            if length_of_data == 0:
                break
            try:
                for invoice in data.get("Invoices", []):
                    first_line_item = invoice.get("LineItems", [])
                    if first_line_item:
                        description = first_line_item[0].get("Description", "")
                        quantity = first_line_item[0].get("Quantity", 0.0)
                        unit_amount = first_line_item[0].get("UnitAmount", 0.0)
                    else:
                        description = ""
                        quantity = 0.0
                        unit_amount = 0.0
                    invoice_id = invoice.get("InvoiceID", "")
                    invoice_type = invoice.get("Type", "")
                    UpdatedDateUTC = format_date(invoice.get("UpdatedDateUTC", ""))
                    contact_name = invoice.get("Contact", {}).get("Name", "")
                    date = format_date(invoice.get("Date", ""))
                    due_date = format_date(invoice.get("DueDate", ""))
                    invoice_number = invoice.get("InvoiceNumber", "")
                    reference = invoice.get("Reference", "")
                    status = invoice.get("Status", "")
                    sub_total = invoice.get("SubTotal", 0.0)
                    total_tax = invoice.get("TotalTax", 0.0)
                    total = invoice.get("Total", 0.0)
                    amount_due = invoice.get("AmountDue", 0.0)
                    amount_paid = invoice.get("AmountPaid", 0.0)
                    fully_paid_on_date = format_date(invoice.get("FullyPaidOnDate", ""))
                    id = invoice_id + str(user_id)
                    has_attachment = invoice.get("HasAttachments", "")
                    if has_attachment:
                        insert_attachments_data(token, tenant, xero_userid, conn, "Invoices", invoice_id)


                    # Check if the invoice already exists
                    cursor.execute("SELECT COUNT(*) FROM Invoices WHERE InvoiceID = ? AND user_id = ?", (invoice_id, user_id))
                    result = cursor.fetchone()

                    if result[0] == 0:  # If invoice ID doesn't exist in the database
                        cursor.execute("""
                            INSERT INTO Invoices (id,InvoiceID, Type, ContactName,DueDate,Date,FullyPaidOndate,  InvoiceNumber, Reference, Status, SubTotal, TotalTax, Total, AmountDue, AmountPaid,xero_userid,user_id,UpdatedDateUTC, Description,Quantity,UnitAmount)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?, ?, ?, ?, ?, ?,?,?,?)
                        """, (id,invoice_id, invoice_type, contact_name, due_date, date, fully_paid_on_date, invoice_number, reference, status, sub_total, total_tax, total, amount_due, amount_paid ,xero_userid,user_id,UpdatedDateUTC, description, quantity,unit_amount))
                        logging.info(f"Invoice API Invoice with ID {invoice_id} inserted successfully.")
                    else:
                        cursor.execute("SELECT UpdatedDateUTC FROM Invoices WHERE InvoiceID = ? AND user_id = ?", (invoice_id, user_id))
                        updated_date_utc_existing = cursor.fetchone()[0]
                        updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                        updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                        created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                        if updated_date_utc_dt == created_date_utc_existing_dt:
                            logging.info(f"Invoice API Invoice with ID {invoice_id} already exists in the database.")
                        else:
                            cursor.execute("""
                                UPDATE Invoices
                                SET Description = ?,Quantity = ?,UnitAmount = ? ,Type = ?, ContactName = ?, DueDate = ?, Date = ?, FullyPaidOndate = ?, InvoiceNumber = ?, Reference = ?, Status = ?,
                                    SubTotal = ?, TotalTax = ?, Total = ?, AmountDue = ?, AmountPaid = ?, xero_userid = ?, UpdatedDateUTC = ?
                                WHERE InvoiceID = ? AND user_id = ?
                            """, (description, quantity,unit_amount , invoice_type, contact_name, due_date, date, fully_paid_on_date, invoice_number, reference, status,
                                sub_total, total_tax, total, amount_due, amount_paid, xero_userid, UpdatedDateUTC, invoice_id, user_id))
                            logging.info(f"Invoice API Invoice with ID {invoice_id} updated successfully.")
                conn.commit()
            except pyodbc.Error as e:
                logging.error(f"Invoice API Database error: {e}")
        cursor.close()
        return True
    except Exception as e:
        logging.error(f"Invoice API error: {e}")
        return False
