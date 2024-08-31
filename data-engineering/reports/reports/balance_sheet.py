import pandas as pd
import pyodbc
import logging
import calendar
from datetime import datetime, timedelta
from .connection import format_date
from utilities import call_api

def insert_balance_sheet_data(token, tenant, xero_userID, conn,user_id):
    try:
        cursor = conn.cursor()
        current_date = datetime.now()
        for i in range(12):
            last_day_of_month = calendar.monthrange(current_date.year, current_date.month)[1]
            last_date_of_month = current_date.replace(day=last_day_of_month)
            date = last_date_of_month.strftime('%Y-%m-%d')
            current_date = current_date.replace(day=1) - timedelta(days=1)
            data_dict = call_api(tenant, token,f"Reports/BalanceSheet?date={date}")
            report = data_dict['Reports'][0]
            UpdatedDateUTC = format_date(report['UpdatedDateUTC'])
            rows = report['Rows']
            headers = []
            account_ids = []
            for cell in rows[0]['Cells']:
                headers.append(cell['Value'])
                if 'Attributes' in cell:
                    account_ids.append(cell['Attributes'][0]['Id'])
                else:
                    account_ids.append(None)

            # Extract data rows and account ids
            data_rows = []
            account_ids_data = []
            for section in rows[1:]:
                if 'Rows' in section:
                    for row in section['Rows']:
                        cells = row['Cells']
                        values = [cell['Value'] for cell in cells]
                        data_rows.append(values)
                        if 'Attributes' in cells[0]:
                            account_ids_data.append(cells[0]['Attributes'][0]['Value'])
                        else:
                            account_ids_data.append(None)

            # Check the number of headers and the length of each data row
            logging.info(f"Balance Sheet Number of headers:{len(headers)}")
            logging.info(f"Balance Sheet Length of each data row: {len(data_rows[0])}")
            # Create DataFrame
            df = pd.DataFrame(data_rows, columns=headers)
            # Add account_id to the DataFrame
            df['Account ID'] = account_ids_data
            logging.info(f"Balance Sheet dataframe :{df}")
            # Iterate over DataFrame rows and insert into the database
            try:
                for index, row in df.iterrows():
                    account_id = row['Account ID']
                    for header in headers[1:]:
                        date_index = headers.index(header)
                        date = headers[date_index]
                        value = row[date]
                        if pd.notnull(value):
                            try:
                                cursor.execute("SELECT COUNT(*) FROM BalanceSheet WHERE account_type = ? AND date = ? AND user_id = ?", (row[headers[0]], date, user_id))
                                if cursor.fetchone()[0] == 0:
                                    # The data does not exist, insert the data
                                    cursor.execute("INSERT INTO BalanceSheet (account_id, account_type, date, value,user_id,UpdatedDateUTC) VALUES (?, ?, ?,?, ?, ?)", (account_id, row[headers[0]], date, value,user_id,UpdatedDateUTC))
                                    conn.commit()
                                    logging.info(f"Inserted new record ")
                                else:
                                    cursor.execute("SELECT UpdatedDateUTC FROM BalanceSheet WHERE account_type = ? AND date = ? AND user_id = ?", (row[headers[0]], date, user_id))
                                    updated_date_utc_existing = cursor.fetchone()[0]
                                    if updated_date_utc_existing != UpdatedDateUTC:
                                        cursor.execute("""
                                            UPDATE BalanceSheet
                                            SET account_id = ?, account_type = ?, date = ?, value = ?, user_id = ?, UpdatedDateUTC = ?
                                            WHERE account_type = ? AND date = ? AND user_id = ?
                                        """, (account_id, row[headers[0]], date, value, user_id, UpdatedDateUTC, row[headers[0]], date, user_id))
                                        conn.commit()
                                        logging.info(f"Updated record with account_type {row[headers[0]]} and date {date}")
                                    else:
                                        # The data exists and UpdatedDateUTC matches
                                        logging.info(f"Data for Balance Sheet with account_type {row[headers[0]]} and date {date} is already up to date in the database.")
                            except pyodbc.Error as db_err:
                                logging.error(f'Balance sheet Database error occurred: {db_err}')
                                cursor.close()
                                return False
            except pyodbc.Error as db_err:
                logging.error(f'Balance Sheet Database error occurred: {db_err}')
                return False
        cursor.close()
        return True
    except Exception as e:
        logging.error(f"Balance Sheet Error: {e}")
