import requests
import pyodbc
import logging
from accounts.accounting.insert_attachments import insert_attachments_data
from accounts.accounting.connection import format_date
import datetime
from utilities import call_api,parse_datetime

def get_contact_data(token, tenant, xero_userID, conn,user_id):
    try:
        cursor = conn.cursor()
        data = call_api(tenant, token,"Contacts")
        for contact in data.get("Contacts", []):
            contact_id = contact.get("ContactID", "")
            UpdatedDateUTC = format_date(contact.get("UpdatedDateUTC", ""))
            name = contact.get("Name", "")
            address_values = []
            for address in contact.get("Addresses", []):
                address_str = f"{address.get('AddressType', '')}: {address.get('AddressLine1', '')} {address.get('AddressLine2', '')} {address.get('City', '')} {address.get('Region', '')} {address.get('PostalCode', '')} {address.get('Country', '')}".strip()
                address_values.append(address_str)
            address_values = '; '.join(address_values)

            phone_values = []
            for phone in contact.get("Phones", []):
                phone_str = f"{phone.get('PhoneType', '')}: ({phone.get('PhoneAreaCode', '')}) {phone.get('PhoneNumber', '')} {phone.get('PhoneCountryCode', '')}".strip()
                phone_values.append(phone_str)
            phone_values = '; '.join(phone_values)
            EmailAddress = contact.get("EmailAddress", "")
            CompanyNumber = contact.get("CompanyNumber", "")
            IsSupplier = contact.get("IsSupplier", "")
            IsCustomer = contact.get("IsCustomer", "")
            has_attachment = contact.get("HasAttachments", "")
            if has_attachment:
                insert_attachments_data(token, tenant, xero_userID, conn, "Contacts", contact_id)
            try:
                cursor.execute("SELECT COUNT(*) FROM contacts WHERE contact_id = ? AND user_id = ?", (contact_id,user_id))
                result = cursor.fetchone()
                if result[0] == 0:  # If contact_id doesn't exist in the database
                    cursor.execute("""

                        INSERT INTO contacts (contact_id, name, address, phone, xero_userID,user_id,IsSupplier,IsCustomer,EmailAddress,CompanyNumber,UpdatedDateUTC)
                        VALUES (?, ?, ?, ?,?, ?,?,?,?,?,?)
                    """, (contact_id, name, address_values, phone_values, xero_userID,user_id,IsSupplier,IsCustomer,EmailAddress,CompanyNumber,UpdatedDateUTC))
                    logging.info(f"Contacts API Contact {name} with ID {contact_id} inserted successfully.")
                else:
                    # Contact exists, check the UpdatedDateUTC
                    cursor.execute("SELECT UpdatedDateUTC FROM contacts WHERE contact_id = ? AND user_id = ?", (contact_id, user_id))
                    updated_date_utc_existing = cursor.fetchone()[0]
                    updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                    updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                    created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                    
                    if updated_date_utc_dt == created_date_utc_existing_dt:
                        logging.info(f"Contacts API Contact with ID {contact_id} already exists in the database.")
                    else:
                        # Update the contact details
                        cursor.execute("""
                            UPDATE contacts
                            SET name = ?, address = ?, phone = ?, xero_userID = ?, IsSupplier = ?, IsCustomer = ?,
                                EmailAddress = ?, CompanyNumber = ?, UpdatedDateUTC = ?
                            WHERE contact_id = ? AND user_id = ?
                        """, (name, address_values, phone_values, xero_userID, IsSupplier, IsCustomer, EmailAddress, CompanyNumber, UpdatedDateUTC, contact_id, user_id))
                        logging.info(f"Contacts API Contact with ID {contact_id} updated successfully.")
            except pyodbc.Error as e:
                logging.error(f"Contacts API Database error: {e}")
                return False
        conn.commit()
        cursor.close()
    
        return True
    except Exception as e:
        logging.error(f"Contacts API Error: {e}")