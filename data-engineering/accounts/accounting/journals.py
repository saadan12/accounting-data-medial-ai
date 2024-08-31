import pyodbc
from accounts.accounting.connection import format_date
import logging
from utilities import call_api
import openai
import os
from dotenv import load_dotenv
load_dotenv()
openai.api_type = str(os.environ["OPENAI_API_TYPE"])
openai.api_key = str(os.environ["OPENAI_API_KEY"])
openai.api_base = str(os.environ["OPENAI_API_BASE"])
openai.api_version = str(os.environ["OPENAI_API_VERSION"])

def openai_nameextractor(details):
    if details:
        message = [{"role": "user", "content": f"Please exclude date and price in the context: context: {details}"}]
        response = openai.chat.completions.create(
                    messages=message,
                    model="gpt-4o",
                    max_tokens=100,
                    temperature=0.4,
                    top_p=0.9
                )
        logging.info(f"Final Result:{response.choices[0].message.content}")
        return response.choices[0].message.content
    else :
        return ""
    
def insert_journals_data(token, tenant, xero_userid, conn, user_id):
    offset_value = 1
    while True:
        try:
            cursor = conn.cursor()
            logging.info("offset " + str(offset_value))
            data = call_api(tenant, token, f"Journals?offset={offset_value}")
            length_of_data = len(data.get("Journals", []))
            if length_of_data == 0:
                break
            offset_value = data.get("Journals", [])[-1].get('JournalNumber')
            contact_name = ''
            bank_transaction_id = None
            payment_id = None
            credit_note_id = None
            invoice_id = None
            try:
                for journal in data.get("Journals", []):
                    journal_id = journal.get("JournalID", "")
                    created_date_utc = format_date(journal.get("CreatedDateUTC", ""))
                    journal_date = format_date(journal.get("JournalDate", ""))
                    journal_lines = journal.get("JournalLines", [])
                    journal_number = journal.get("JournalNumber", 0)
                    reference = journal.get("Reference", "")
                    source_id = journal.get("SourceID", "")
                    source_type = journal.get("SourceType", "")
                    
                    if source_id and source_type:
                        if source_type in ['ACCPAY', 'ACCREC']:
                            data = call_api(tenant, token, f"Invoice/{source_id}")
                            invoice = data.get("Invoices", [])[0]
                            contact_name = invoice.get("Contact", {}).get("Name")
                            invoice_id = source_id + str(user_id)
                            logging.info("Invoice " + str(contact_name))
                        elif source_type in ['ACCPAYCREDIT', 'ACCRECCREDIT']:
                            data = call_api(tenant, token, f"CreditNotes/{source_id}")
                            credit_note = data.get("CreditNotes", [])[0]
                            contact_name = credit_note.get("Contact", {}).get("Name")
                            credit_note_id = source_id + str(user_id)
                            logging.info("Credit Notes " + str(contact_name))
                        elif source_type in ['CASHPAID', 'CASHREC']:
                            data = call_api(tenant, token, f"BankTransactions/{source_id}")
                            bank_transaction = data.get("BankTransactions", [])[0]
                            contact_name = bank_transaction.get("Contact", {}).get("Name", "")
                            bank_transaction_id = source_id + str(user_id)
                        elif source_type in ['ACCPAYPAYMENT', 'ACCRECPAYMENT']:
                            data = call_api(tenant, token, f"Payments/{source_id}")
                            contact_name = data["Payments"][0]["Invoice"]["Contact"]["Name"]
                            payment_id = source_id + str(user_id)
                            logging.info("Payments " + str(contact_name))

                        elif source_type == 'TRANSFER' and source_type is not None:
                            data = call_api(tenant, token,f"Banktransactions/{source_id}/history")
                            contact_name = openai_nameextractor(data.get('HistoryRecords', [])[0].get('Details', ''))
                            logging.info("Banktransactions history " + str(contact_name))
                        elif source_type == 'EXPCLAIM' and source_type is not None:
                            data = call_api(tenant, token,f"ExpenseClaims/{source_id}/History")
                            contact_name=openai_nameextractor(data['HistoryRecords'][0]['Details'] if data['HistoryRecords'] else None)
                            logging.info("ExpenseClaims History " + str(contact_name))

                    else:
                        print("No source_id and source_type")
                        contact_name = ""
 
                    cursor.execute("SELECT COUNT(*) FROM Journals WHERE JournalID = ? AND user_id =? AND JournalNumber =? AND JournalDate = ? ", (journal_id, user_id, journal_number, journal_date))
                    result = cursor.fetchone()
                    if result[0] == 0:  # If journal ID doesn't exist in the database
                        for line in journal_lines:
                            journal_line_id = line.get("JournalLineID", "")
                            account_id = line.get("AccountID", "")
                            account_code = line.get("AccountCode", "")
                            account_type = line.get("AccountType", "")
                            account_name = line.get("AccountName", "")
                            description = line.get("Description", "")
                            net_amount = line.get("NetAmount", 0.0)
                            gross_amount = line.get("GrossAmount", 0.0)
                            tax_amount = line.get("TaxAmount", 0.0)
                            tax_type = line.get("TaxType", "")
                            tax_name = line.get("TaxName", "")
                            try:
                                cursor.execute("""
                                    INSERT INTO Journals (
                                        JournalID, CreatedDateUTC, JournalDate, JournalNumber,
                                        Reference, SourceID, SourceType, ContactName, xero_userID, user_id,
                                        JournalLineID, AccountID, AccountCode, AccountType, AccountName,
                                        Description, NetAmount, GrossAmount, TaxAmount, TaxType, TaxName,Bank_Transactions_id,payment_id,credit_notes_id,invoice_id
                                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?, ?)
                                """, (journal_id, created_date_utc, journal_date, journal_number, reference, source_id, source_type, contact_name, xero_userid, user_id,
                                    journal_line_id, account_id, account_code, account_type, account_name,
                                    description, net_amount, gross_amount, tax_amount, tax_type, tax_name,bank_transaction_id,payment_id,credit_note_id,invoice_id))
                                conn.commit()
                                logging.info(f"JournalEntry with ID {journal_id} inserted successfully.")
                            except Exception as e:
                                logging.info(f"Error {payment_id}")
                        bank_transaction_id = None
                        payment_id = None
                        credit_note_id = None
                        invoice_id = None
                    else:
                        logging.info(f"JournalEntry with ID {journal_id} already exists in the database.")
                    contact_name = ""
                   
                # conn.commit()
                cursor.close()
            except pyodbc.Error as e:
                logging.error(f"Journals API Database error: {e}")
        except Exception as e:
            logging.error(f"Journals API Error: {e}")
            return False
    return True