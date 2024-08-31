import requests
from accounts.accounting.insert_attachments import insert_attachments_data
import logging
from accounts.accounting.connection import format_date
from utilities import call_api,parse_datetime

    
def get_account_data(token, tenant,xero_userID, conn,user_id):
    try:
        cursor = conn.cursor()
        data = call_api(tenant, token,"Accounts")
        logging.info(f"Accounts api response: {data}")
        # Extract relevant data and insert into databasefor account in data.get("Accounts", []):
        for account in data.get("Accounts", []):
            code = account.get("Code", "")
            name = account.get("Name", "")
            UpdatedDateUTC = format_date(account.get("UpdatedDateUTC", ""))
            description = account.get("Description", "")
            account_class = account.get("Class", "")
            account_id = account.get("AccountID", "")  # Assuming "AccountId" is the attribute containing the account ID
            has_attachment = account.get("HasAttachments", "")
            if has_attachment:
                insert_attachments_data(token, tenant, xero_userID, conn, "Accounts", account_id)
            # Check if the account ID exists in the database
            cursor.execute("SELECT COUNT(*) FROM accounts WHERE account_id = ? AND user_id = ?", (account_id,user_id))
            result = cursor.fetchone()
            if result[0] == 0:  # If account ID doesn't exist in the database
                # Insert the account details into the database
                cursor.execute("""
                    INSERT INTO accounts (code, name, description, accounts_class, account_id, xero_userID,user_id,UpdatedDateUTC)
                    VALUES (?, ?, ?, ?, ?, ?, ? ,?)
                """, (code, name, description, account_class, account_id, xero_userID,user_id,UpdatedDateUTC))
                logging.info(f"Accounts API Account with ID {account_id} inserted successfully.")
            else:
                cursor.execute("SELECT UpdatedDateUTC FROM accounts WHERE account_id = ? AND user_id =?", (account_id, user_id))
                updated_date_utc_existing = cursor.fetchone()[0]
                updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                if updated_date_utc_dt == created_date_utc_existing_dt:
                    logging.info(f"Accounts with ID {account_id} already exists in the database.")
                else:
                    cursor.execute("""
                        UPDATE accounts
                        SET code = ?, name = ?, description = ?, accounts_class = ?, xero_userID = ?, UpdatedDateUTC = ?
                        WHERE account_id = ? AND user_id = ?
                    """, (code, name, description, account_class, xero_userID, UpdatedDateUTC, account_id, user_id))
                    logging.info(f"Accounts API Account with ID {account_id} updated successfully.")
           
        # Commit transaction and close connection
        conn.commit()
        cursor.close()
        return True
    except Exception as e:
        logging.error(f"Accounts API Error: {e}")
