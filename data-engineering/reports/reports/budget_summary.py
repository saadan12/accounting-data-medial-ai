import pandas as pd
import requests
import pyodbc
import logging
from datetime import datetime
from .connection import format_date
from utilities import call_api

def get_budget_summary_data(token, tenant, xero_userid, conn,user_id):
    try:
        cursor = conn.cursor()
        current_year = datetime.now().strftime('%Y')
        data_dict = call_api(tenant, token,f"Reports/BudgetSummary?date={current_year}-01-01")
        report = data_dict['Reports'][0]
        UpdatedDateUTC = format_date(report['UpdatedDateUTC'])
        logging.info("UpdatedDateUTC " + UpdatedDateUTC)
        rows = report['Rows']
        
        headers = [cell['Value'] for cell in rows[0]['Cells']]
        
        data_rows = []
        for section in rows[1:]:
            if 'Rows' in section:
                for row in section['Rows']:
                    cells = row['Cells']
                    values = [cell['Value'] for cell in cells]
                    data_rows.append(values)

        # Create DataFrame
        df = pd.DataFrame(data_rows, columns=headers)
        logging.info(f"Budget Summary API DataFrame: {df}")
        for index, row in df.iterrows():
            for date in headers[1:]:  
                value = row[date]
                if pd.notnull(value):
                    try:
                        # Check if the combination of type, date, and user_id already exists
                        cursor.execute("SELECT COUNT(*) FROM BudgetSummary WHERE account = ? AND date = ? AND user_id = ?", (row[headers[0]], date, user_id))
                        if cursor.fetchone()[0] == 0:
                            # The data does not exist, insert the data
                            cursor.execute("INSERT INTO BudgetSummary (account, date, value, user_id,UpdatedDateUTC) VALUES (?, ?, ?, ?, ?)", (row[headers[0]], date, value, user_id,UpdatedDateUTC))
                            conn.commit()
                            logging.info(f"Inserted new record with type: {row[headers[0]]}, date: {date}, user_id: {user_id}")
                        else:
                            cursor.execute("SELECT UpdatedDateUTC FROM BudgetSummary WHERE account = ? AND date = ? AND user_id = ?", (row[headers[0]], date, user_id))
                            db_updated_date_utc = cursor.fetchone()[0]
                            if db_updated_date_utc != UpdatedDateUTC:
                                cursor.execute("""
                                    UPDATE BudgetSummary
                                    SET account = ?, date = ?, value = ?, user_id = ?, UpdatedDateUTC = ?
                                    WHERE account = ? AND date = ? AND user_id = ?
                                """, (row[headers[0]], date, value, user_id, UpdatedDateUTC, row[headers[0]], date, user_id))
                                conn.commit()
                                logging.info(f"Updated record with account: {row[headers[0]]}, date: {date}, user_id: {user_id}")
                            else:
                                logging.info(f"Data for account {row[headers[0]]}, date {date}, user_id {user_id} is already stored in the database.")
                    except pyodbc.Error as db_err:
                        logging.error(f'Budget Summary Database error occurred: {db_err}')
                        cursor.close()
                        return False
        cursor.close()
        return True
    except Exception as e:
        logging.error(f"Budget Summary API Error: {e}")


