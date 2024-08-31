import pandas as pd
import logging
import time
from accounts.accounting.connection import extract_user_id
from datetime import datetime, timedelta
from utilities import call_api,format_date
import os
from dotenv import load_dotenv
load_dotenv()
 
def insert_aged_payables_by_contact_data(token, tenant, xero_userid, conn, user_id):
    cursor = conn.cursor()
    data = call_api(tenant, token,"Contacts")
    logging.info(f"response: {data}")
    for index, contact in enumerate(data.get("Contacts", [])):
        contact_id = contact.get("ContactID", "")
        # may be used later
        # to_date = datetime.now()
        # from_date = to_date - timedelta(days=1*365)
        # from_date_str = from_date.strftime('%Y-%m-%d')
        # to_date_str = to_date.strftime('%Y-%m-%d')
        url = f"{os.getenv('BASE_URL')}/Reports/AgedPayablesByContact?ContactID={contact_id}"
        split_index = url.index('Reports/')
        report_endpoint = url[split_index:]
        data_dict = call_api(tenant, token,report_endpoint)
        report = data_dict.get('Reports', [{}])[0]
        UpdatedDateUTC = format_date(report['UpdatedDateUTC'])
        rows = report.get('Rows', [])
        headers = [cell.get('Value', '') for cell in rows[0].get('Cells', [])]
        headers.extend(['InvoiceID', 'ReportTitles'])
        try:
            for row in rows:
                if 'Rows' in row:
                    for sub_row in row['Rows']:
                        if sub_row['RowType'] == 'Row':
                            cells = sub_row.get('Cells', [])
                            row_data = [cell.get('Value', '') for cell in cells]
                            while len(row_data) < len(headers) - 1:
                                row_data.append('')
                            invoice_id = cells[0].get('Attributes', [{}])[0].get('Value', '') if cells else ''
                            row_data.append(invoice_id)
                            row_data.extend(report.get('ReportTitles', ['', '', '', ''])[:4])
                            if len(row_data) < 14:  # Check if row_data has enough elements
                                logging.warning(f"Row data has insufficient elements: {row_data}")
                                continue
                            conn.autocommit = True
                            logging.info("**********************")
                            logging.info(row_data)
                            logging.info("**********************")
                            cursor.execute("SELECT COUNT(*) FROM AgedPayablesByContact WHERE DueDate = ? AND  user_id = ? AND name = ? AND Contact_ID = ? AND InvoiceID = ? ", (row_data[2],  user_id, row_data[11], contact_id,invoice_id))
                            if cursor.fetchone()[0] == 0:
                                try:
                                    cursor.execute("""
                                        INSERT INTO AgedPayablesByContact (Date, Reference, DueDate, Total, Paid, Credited, Due, InvoiceID, user_id, type, name, ReportTitleDate, description,Contact_ID,UpdatedDateUTC)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
                                    """, (row_data[0], row_data[1], row_data[2], row_data[4], row_data[5], row_data[6], row_data[7], invoice_id, user_id, row_data[10], row_data[11], row_data[12], row_data[13],contact_id,UpdatedDateUTC))
                                    conn.commit()
                                    logging.info("Inserted new record")
                                except Exception as e:
                                    print("Insertion Error ", e)
                            else:
                                cursor.execute("SELECT UpdatedDateUTC FROM AgedPayablesByContact WHERE DueDate = ? AND user_id = ? AND name = ? AND Contact_ID = ?",
                                            (row_data[2], user_id, row_data[11], contact_id))
                                updated_date_utc_existing = cursor.fetchone()[0]
                                if updated_date_utc_existing != UpdatedDateUTC:
                                    # The data exists but UpdatedDateUTC does not match, so update it
                                    cursor.execute("""
                                        UPDATE AgedPayablesByContact
                                        SET Date = ?, Reference = ?, Total = ?, Paid = ?, Credited = ?, Due = ?, type = ?, name = ?, ReportTitleDate = ?, description = ?, UpdatedDateUTC = ?
                                        WHERE DueDate = ? AND user_id = ? AND InvoiceID = ? AND Contact_ID = ?
                                    """, (
                                        row_data[0], row_data[1], row_data[4], row_data[5], row_data[6], row_data[7], row_data[10], row_data[11],
                                        row_data[12], row_data[13], UpdatedDateUTC, row_data[2], user_id, invoice_id, contact_id
                                    ))
                                    conn.commit()
                                    logging.info(f"Updated record for InvoiceID {invoice_id} and Contact_ID {contact_id}")
                                else:
                                    # The data exists and UpdatedDateUTC matches
                                    logging.info(f"Data for DueDate {row_data[2]}, name {row_data[11]}, InvoiceID {invoice_id}, Contact_ID {contact_id} is already up to date in the database.")
        except Exception as e:
            logging.error(f"AgedPayablesByContact API Insertion error: {e}")
            conn.rollback()
    logging.info("AgedPayablesByContact API data inserted")
