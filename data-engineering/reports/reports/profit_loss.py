import pandas as pd
import time
import logging
import datetime
import calendar
from .connection import format_date
import datetime
from utilities import call_api,parse_datetime
import os
from dotenv import load_dotenv
load_dotenv()

def generate_urls():
    current_date = datetime.date.today()
    urls = []
    while current_date.year == datetime.date.today().year or current_date.month != 1:
        last_day_of_month = calendar.monthrange(current_date.year, current_date.month)[1]
        from_date = current_date.replace(day=1)
        to_date = current_date.replace(day=last_day_of_month)
        from_date_str = from_date.strftime('%Y-%m-%d')
        to_date_str = to_date.strftime('%Y-%m-%d')
        logging.info("from_date_str" + str(from_date_str))
        logging.info("to_date_str" + str(to_date_str))
        url = f"{os.getenv('BASE_URL')}Reports/ProfitAndLoss?fromDate={from_date_str}&toDate={to_date_str}"
        urls.append(url)
        if current_date.month == 1:
            current_date = current_date.replace(year=current_date.year - 1, month=12)
        else:
            current_date = current_date.replace(month=current_date.month - 1)

    return urls


def insert_profit_and_loss_data(token, tenant, conn,user_id):
    cursor = conn.cursor()
    try:
        # Generate the URLs
        urls = generate_urls()
        for url in urls:
            logging.info(f"Fetchable url: {url}")
            split_index = url.index('Reports/')
            report_endpoint = url[split_index:]
            data_dict = call_api(tenant, token,report_endpoint)
            
            logging.info(data_dict)

            id=data_dict.get('Id')
            report = data_dict['Reports'][0]
            UpdatedDateUTC = format_date(report['UpdatedDateUTC'])
            logging.info("UpdatedDateUTC " + UpdatedDateUTC)
            rows = report['Rows']
            headers = [cell['Value'] for cell in rows[0]['Cells']]
            headers.append('AccountID')
            for section in rows[1:]:
                if 'Rows' in section:
                    for row in section['Rows']:
                        cells = row['Cells']
                        values = [cell['Value'] for cell in cells]
                        account_id = cells[0]['Attributes'][0]['Value'] if 'Attributes' in cells[0] else ''
                        values.append(account_id)
                        values.append(id)
                        values.append(report.get('ReportTitles')[0])
                        values.append(report.get('ReportTitles')[1])
                        values.append(report.get('ReportTitles')[2])
                        try:
                            cursor.execute("SELECT COUNT(*) FROM ProfitAndLossHistorical WHERE Type = ? AND ReportDates = ? AND user_id = ?", (values[0],values[6], user_id))
                            result = cursor.fetchone()
                            if result[0] == 0:  # If record doesn't exist in the database
                                cursor.execute("""
                                    INSERT INTO ProfitAndLossHistorical (Type, Value, AccountID, ReportID, ReportTitle, Organisation, ReportDates, user_id,UpdatedDateUTC)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)
                                """, (values[0], values[1], values[2], values[3], values[4], values[5], values[6], user_id,UpdatedDateUTC))
                                conn.commit()
                                print("data inserted")
                        except Exception as e:
                            logging.info(f"Error {e}")
                        else:
                            cursor.execute("SELECT UpdatedDateUTC FROM ProfitAndLossHistorical WHERE Type = ? AND ReportDates = ? AND user_id = ?", (values[0], values[6], user_id))
                            updated_date_utc_existing = cursor.fetchone()[0]

                            # Parse the datetime strings to datetime objects for comparison
                            updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                            updated_date_utc_existing_dt = parse_datetime(updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S"))
                            if updated_date_utc_dt == updated_date_utc_existing_dt:
                                logging.info(f"Record with Type {values[0]} and Date {values[6]} already exists in the database.")
                            else:
                                cursor.execute("""
                                    UPDATE ProfitAndLossHistorical
                                    SET Value = ?, AccountID = ?, ReportID = ?, ReportTitle = ?, Organisation = ?, UpdatedDateUTC = ?
                                    WHERE Type = ? AND ReportDates = ? AND user_id = ?
                                """, (values[1], values[2], values[3], values[4], values[5], UpdatedDateUTC, values[0], values[6], user_id))
                                conn.commit()
                                logging.info(f"Record with Type {values[0]} and Date {values[6]} updated successfully.")
            # time.sleep(2)         
        cursor.close()
        return True
    except Exception as e:
            logging.error(f"Error fetching in Profit and Loss API " + e)


