import pandas as pd
import pyodbc
import logging
from datetime import datetime, timedelta
import calendar
from .connection import format_date
from utilities import call_api

def insert_trial_balance_data(token, tenant, conn,user_id):
    try:
        cursor = conn.cursor()
        today = datetime.now()
        one_year_ago = today - timedelta(days=365)
        
        # Start from the end of the current month
        current_date = datetime(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        
        while current_date >= one_year_ago:

            date = current_date.strftime('%Y-%m-%d')
            first_day_of_current_month = datetime(current_date.year, current_date.month, 1)
            current_date = first_day_of_current_month - timedelta(days=1)
            current_date = datetime(current_date.year, current_date.month, calendar.monthrange(current_date.year, current_date.month)[1])
            data_dict = call_api(tenant, token,"Reports/TrialBalance")
            report = data_dict['Reports'][0]
            rows = report['Rows']
            headers = []
            for cell in rows[0]['Cells']:
                headers.append(cell['Value'])
            report = data_dict['Reports'][0]
            UpdatedDateUTC = format_date(report['UpdatedDateUTC'])
            rows = report['Rows']
            
            headers = []
            for cell in rows[0]['Cells']:
                headers.append(cell['Value'])
            
            data_rows = []
            account_ids = []
            for section in rows[1:]:
                if 'Rows' in section:
                    for row in section['Rows']:
                        cells = row['Cells']
                        values = [cell['Value'] for cell in cells]
                        data_rows.append(values)
                        # Extract account_id if available
                        account_id = cells[0]['Attributes'][0]['Value'] if 'Attributes' in cells[0] else None
                        account_ids.append(account_id)

            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=headers)
            df['Account ID'] = account_ids  # Add account_id column
            # Iterate over DataFrame rows and insert into the database
            for index, row in df.iterrows():
                try:
                    cursor.execute("SELECT COUNT(*) FROM TrialBalance WHERE Account_ID = ? AND user_id = ?", (row['Account ID'],user_id))
                    if cursor.fetchone()[0] == 0:
                        # Account_ID does not exist, insert the data
                        cursor.execute("INSERT INTO TrialBalance (Debit, Credit, YTD_Debit, YTD_Credit, Account_ID, user_id,ReportDate,UpdatedDateUTC) VALUES (?, ?, ?, ?, ?, ?,?,?)",
                                    (row['Debit'], row['Credit'], row['YTD Debit'], row['YTD Credit'], row['Account ID'], user_id,date,UpdatedDateUTC))
                        cursor.commit()
                        logging.info(f"Inserted new record with Account_ID: {row['Account ID']}")
                    else:
                        cursor.execute("SELECT UpdatedDateUTC FROM TrialBalance WHERE Account_ID = ? AND user_id = ?", (row['Account ID'], user_id))
                        db_updated_date_utc = cursor.fetchone()[0]
                        # Compare if db_updated_date_utc is not None and different from UpdatedDateUTC
                        if db_updated_date_utc is not None and db_updated_date_utc != UpdatedDateUTC:
                            cursor.execute("""
                                UPDATE TrialBalance
                                SET Debit = ?, Credit = ?, YTD_Debit = ?, YTD_Credit = ?, UpdatedDateUTC = ?
                                WHERE Account_ID = ? AND user_id = ?
                            """, (row['Debit'], row['Credit'], row['YTD Debit'], row['YTD Credit'], UpdatedDateUTC, row['Account ID'], user_id))
                            conn.commit()
                            logging.info(f"Updated record with Account_ID: {row['Account ID']}")
                        else:
                            logging.info(f"Data for Account_ID {row['Account ID']} is already stored in the database.")
                except pyodbc.Error as db_err:
                    logging.error(f'Trial Balance Database error occurred: {db_err}')
        cursor.close()
        return True
    except Exception as e:
        logging.error(f"Error fetching in Trial Balancee API")
