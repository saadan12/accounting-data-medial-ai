import requests
import pyodbc
import json
from accounts.accounting.connection import format_date
import logging
import datetime
from utilities import call_api,parse_datetime

def get_expense_claim_data(token, tenant, xero_userID, conn,user_id):
    try:
        cursor = conn.cursor()
        
        data = call_api(tenant, token,"ExpenseClaims")

        try:
            for expense_claim in data.get("ExpenseClaims", []):
                expense_claim_id = expense_claim.get("ExpenseClaimID", "")
                UpdatedDateUTC = format_date(expense_claim.get("UpdatedDateUTC", ""))
                status = expense_claim.get("Status", "")
                payment_due_date = format_date(expense_claim.get("PaymentDueDate", ""))
                ReportingDate = format_date(expense_claim.get("ReportingDate", ""))
                user = json.dumps(expense_claim.get("User", {}))
                total = expense_claim.get("Total", 0.0)
                amount_due = expense_claim.get("AmountDue", 0.0)
                amount_paid = expense_claim.get("AmountPaid", 0.0)
                
                
            

                # Check if the expense claim already exists
                cursor.execute("SELECT COUNT(*) FROM ExpenseClaims WHERE ExpenseClaimID = ? AND user_id = ?", (expense_claim_id,user_id))
                result = cursor.fetchone()
                if result[0] == 0:
                    cursor.execute("""
                        INSERT INTO ExpenseClaims (ExpenseClaimID, Status, PaymentDuedate, users, Total, AmountDue, AmountPaid, XeroUserID,user_id,ReportingDate,UpdatedDateUTC)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (expense_claim_id, status, payment_due_date, user, total, amount_due, amount_paid, xero_userID,user_id,ReportingDate,UpdatedDateUTC))
                    logging.info(f"Expense Claims API Expense claim with ID {expense_claim_id} inserted successfully.")
                else:
                    cursor.execute("SELECT UpdatedDateUTC FROM ExpenseClaims WHERE ExpenseClaimID = ? AND user_id = ?", (expense_claim_id, user_id))
                    updated_date_utc_existing = cursor.fetchone()[0]
                    updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                    updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                    created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                    
                    if updated_date_utc_dt == created_date_utc_existing_dt:
                        logging.info(f"Expense Claims API Expense claim with ID {expense_claim_id} already exists in the database.")
                    else:
                        cursor.execute("""
                            UPDATE ExpenseClaims
                            SET Status = ?, PaymentDuedate = ?, users = ?, Total = ?, AmountDue = ?, AmountPaid = ?, XeroUserID = ?, ReportingDate = ?, UpdatedDateUTC = ?
                            WHERE ExpenseClaimID = ? AND user_id = ?
                        """, (status, payment_due_date, user, total, amount_due, amount_paid, xero_userID, ReportingDate, UpdatedDateUTC, expense_claim_id, user_id))
                        logging.info(f"Expense Claims API Expense claim with ID {expense_claim_id} updated successfully.")

            conn.commit()
            cursor.close()
            return True
        except pyodbc.Error as e:
            logging.error(f"Expense Claims API Database error: {e}")
            return False
    except Exception as e:
        logging.error(f"Expense Claims API error: {e}")
