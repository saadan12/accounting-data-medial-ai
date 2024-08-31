import pyodbc
import requests
import logging
import os
from dotenv import load_dotenv
load_dotenv()

def insert_attachments_data(token, tenant, xero_userid, conn, end_pint, guid):
    try:
        cursor = conn.cursor()

        url = f"{os.getenv('BASE_URL')}{end_pint}/{guid}/Attachments"
        headers = {
            'xero-tenant-id': tenant,
            'Authorization': f'Bearer {token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json',
        }
        response = requests.get(url, headers=headers)
        data = response.json()

        try:
            for attachment in data.get("Attachments", []):
                attachment_id = attachment.get("AttachmentID", "")
                file_name = attachment.get("FileName", "")
                url = attachment.get("Url", "")
                mime_type = attachment.get("MimeType", "")
                content_length = int(attachment.get("ContentLength", 0))

                # Check if the attachment already exists
                cursor.execute("SELECT COUNT(*) FROM Attachments WHERE AttachmentID = ?", (attachment_id,))
                result = cursor.fetchone()

                if result[0] == 0:  # If attachment ID doesn't exist in the database
                    cursor.execute("""
                        INSERT INTO Attachments (
                            AttachmentID, FileName, Url, MimeType, ContentLength,xero_userID
                        ) VALUES (?, ?, ?, ?, ?,?)
                    """, (attachment_id, file_name, url, mime_type, content_length,xero_userid))
                    logging.info(f"Attachments API Attachment with ID {attachment_id} inserted successfully.")
                else:
                    logging.info(f"Attachments API Attachment with ID {attachment_id} already exists in the database.")

            conn.commit()
            return True
        except pyodbc.Error as e:
            logging.error(f"Attachments API Database error: {e}")
            return False
    except Exception as e:
        logging.error(f"Insert Attachments API Error: {e}")