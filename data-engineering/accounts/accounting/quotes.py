import pyodbc
import json
from accounts.accounting.connection import format_date
import logging
from utilities import call_api,parse_datetime
    
def insert_quotes_data(token, tenant, xero_userid, conn,user_id):
    try:
        cursor = conn.cursor()
        data = call_api(tenant, token,"Quotes")
        logging.info("Data "+ str(data))
        try:
            for quote in data.get("Quotes", []):
                quote_id = quote.get("QuoteID", "")
                quotes_json = json.dumps(quote)
                provider_name = quote.get("Contact", {}).get("Name", "")
                date_string = format_date(quote.get("Date", ""))
                UpdatedDateUTC = format_date(quote.get("UpdatedDateUTC", ""))
                
                # Check if the quote already exists
                cursor.execute("SELECT COUNT(*) FROM Quotes WHERE QuoteID = ? AND user_id = ?", (quote_id,user_id))
                result = cursor.fetchone()

                if result[0] == 0:  # If QuoteID doesn't exist in the database
                    cursor.execute("""
                        INSERT INTO Quotes (providerName, DateTimeUTC, QuoteID, Quotes,xero_userID,user_id,UpdatedDateUTC)
                        VALUES (?, ?, ?, ?, ?, ?,?)
                    """, (provider_name, date_string, quote_id, quotes_json,xero_userid,user_id,UpdatedDateUTC))
                    logging.info(f"Quotes with ID {quote_id} inserted successfully.")
                else:
                    cursor.execute("SELECT UpdatedDateUTC FROM Quotes WHERE QuoteID = ? AND user_id = ?", (quote_id, user_id))
                    updated_date_utc_existing = cursor.fetchone()[0]

                    # Parse the datetime strings to datetime objects for comparison
                    updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                    updated_date_utc_existing_dt = parse_datetime(updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S"))

                    if updated_date_utc_dt == updated_date_utc_existing_dt:
                        logging.info(f"Quotes with ID {quote_id} already exists in the database.")
                    else:
                        cursor.execute("""
                            UPDATE Quotes
                            SET providerName = ?, DateTimeUTC = ?, Quotes = ?, xero_userID = ?, UpdatedDateUTC = ?
                            WHERE QuoteID = ? AND user_id = ?
                        """, (provider_name, date_string, quotes_json, xero_userid, UpdatedDateUTC, quote_id, user_id))
                        logging.info(f"Quotes with ID {quote_id} updated successfully.")
            conn.commit()
            cursor.close()
            
            return True
        except pyodbc.Error as e:
            logging.error(f"Quotes API Database error: {e}")
            return False
    except Exception as e:
        logging.error(f"Quotes API Error: {e}")