import logging
import pandas as pd
import time
from datetime import datetime, timedelta
from utilities import call_api,format_date
import os
from dotenv import load_dotenv
load_dotenv()
 
 
 
def insert_aged_receiveable_by_contact_data(token, tenant, xero_userid, conn, user_id):
    cursor = conn.cursor()
    data = call_api(tenant, token,"Contacts")
    for contact in data.get("Contacts", []):
        contact_id = contact.get("ContactID", "")
        to_date = datetime.now()
        from_date = to_date - timedelta(days=1*365)
        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')
 
        url = f"{os.getenv('BASE_URL')}Reports/AgedReceivablesByContact?ContactID={contact_id}&fromDate={from_date_str}&toDate={to_date_str}"
        split_index = url.index('Reports/')
        report_endpoint = url[split_index:]
 
        data_dict = call_api(tenant, token,report_endpoint)
        logging.info("Data " + str(data_dict))  # Convert dict to string
        report = data_dict['Reports'][0]
        UpdatedDateUTC = format_date(report['UpdatedDateUTC'])
        rows = report['Rows']
        headers = [cell['Value'] for cell in rows[0]['Cells']]
        headers.append('type')
        headers.append('name')
        headers.append('ReportTitlesDate')
        headers.append('description')
 
        # Extract data rows
        for row in rows:
            if 'Rows' in row:
                for sub_row in row['Rows']:
                    if sub_row['RowType'] == 'Row':
                        cells = sub_row['Cells']
                        row_data = [cell.get('Value', '') for cell in cells]
                        invoice_id = cells[0]['Attributes'][0]['Value'] if 'Attributes' in cells[0] else ''
                        row_data.append(invoice_id)
                        row_data.append(report['ReportTitles'][0])
                        row_data.append(report['ReportTitles'][1])
                        row_data.append(report['ReportTitles'][2])
                        row_data.append(report['ReportTitles'][3])
                        logging.info("*************************")
                        logging.info("Row data " + str(row_data))
                        logging.info("*************************")
                        # Check if the invoice_id already exists in the database
                        cursor.execute("SELECT COUNT(*) FROM AgedReceivablesByContact WHERE  Number = ?  AND InvoiceID = ?", (row_data[1],row_data[8],))
                        if cursor.fetchone()[0] == 0:
                            try:
                                cursor.execute("""
                                    INSERT INTO AgedReceivablesByContact (Date, Number, DueDate, Overdue, Total, Paid, Credited, Due, InvoiceID, user_id, type, name, ReportTitleDate, description,UpdatedDateUTC)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
                                """, (row_data[0], row_data[1], row_data[2], row_data[3], row_data[4], row_data[5], row_data[6], row_data[7], row_data[8], user_id, row_data[9], row_data[10], row_data[11], row_data[12],UpdatedDateUTC))
                                conn.commit()
                                logging.info("Inserted new record with Number: " + row_data[1])
                            except Exception as e:
                                print("Insert Error as ", e)
                        else:
                            cursor.execute("SELECT UpdatedDateUTC FROM AgedReceivablesByContact WHERE Number = ? AND InvoiceID = ?", (row_data[1], row_data[8]))
                            updated_date_utc_existing = cursor.fetchone()[0]
                            if updated_date_utc_existing != UpdatedDateUTC:
                                try:
                                    cursor.execute("""
                                        UPDATE AgedReceivablesByContact
                                        SET Date = ?, DueDate = ?, Overdue = ?, Total = ?, Paid = ?, Credited = ?, Due = ?, user_id = ?, type = ?, name = ?, ReportTitleDate = ?, description = ?, UpdatedDateUTC = ?
                                        WHERE Number = ? AND InvoiceID = ?
                                    """, (row_data[0], row_data[2], row_data[3], row_data[4], row_data[5], row_data[6], row_data[7], user_id,row_data[9], row_data[10], row_data[11], row_data[12], UpdatedDateUTC, row_data[1], row_data[8]))
                                    conn.commit()
                                    logging.info(f"Updated record for Number: {row_data[1]} and InvoiceID: {row_data[8]}")
                                except Exception as e:
                                    logging.info("Exception " + str(e))
                            else:
                                logging.info(f"Data for Number: {row_data[1]} and InvoiceID: {row_data[8]} is already up to date in the database.")
    logging.info("AgedReceivablesByContact API data inserted")
    cursor.close()
    return True
 