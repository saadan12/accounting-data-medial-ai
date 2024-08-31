import pyodbc
import json
import requests
from accounts.accounting.connection import format_date
import logging
import datetime
from utilities import call_api,parse_datetime
    
def insert_budgets_data(token, tenant,xero_userid, conn,user_id):
    try:
        cursor = conn.cursor()
        data = call_api(tenant, token,"Budgets")

        try:
            for budget in data.get("Budgets", []):
                budget_id = budget.get("BudgetID", "")
                budget_type = budget.get("Type", "")
                description = budget.get("Description", "")
                updated_date_utc = format_date(budget.get("UpdatedDateUTC", ""))
                # Convert BudgetLines and Tracking to JSON strings
                budget_lines_json = json.dumps(budget.get("BudgetLines", []))
                tracking_json = json.dumps(budget.get("Tracking", []))
                id = budget_id + str(user_id)
                # Check if the budget already exists
                cursor.execute("SELECT COUNT(*) FROM Budgets WHERE BudgetID = ? AND user_id = ?", (budget_id,user_id))
                result = cursor.fetchone()

                if result[0] == 0:  # If budget ID doesn't exist in the database
                    cursor.execute("""
                        INSERT INTO Budgets (
                            BudgetID, Type, Description, UpdatedDateUTC, BudgetLinesJSON, TrackingJSON,xero_userID,user_id,id
                        ) VALUES (?, ?, ?, ?, ?, ?,?,?,?)
                    """, (budget_id, budget_type, description, updated_date_utc, budget_lines_json, tracking_json,xero_userid,user_id,id))
                    logging.info(f"Budgets API Budget with ID {budget_id} inserted successfully.")
                else:
                    cursor.execute("SELECT UpdatedDateUTC FROM Budgets WHERE BudgetID = ? AND user_id = ?", (budget_id, user_id))
                    updated_date_utc_existing = cursor.fetchone()[0]
                    updated_date_utc_dt = parse_datetime(updated_date_utc)
                    updated_date_utc_existing_dt = parse_datetime(updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S"))
                    if updated_date_utc_dt == updated_date_utc_existing_dt:
                        logging.info(f"Budgets API Budget with ID {budget_id} already exists in the database.")
                    else:
                        cursor.execute("""
                            UPDATE Budgets
                            SET Type = ?, Description = ?, UpdatedDateUTC = ?, BudgetLinesJSON = ?, TrackingJSON = ?, xero_userID = ?
                            WHERE BudgetID = ? AND user_id = ?
                        """, (budget_type, description, updated_date_utc, budget_lines_json, tracking_json, xero_userid, budget_id, user_id))
                        logging.info(f"Budgets API Budget with ID {budget_id} updated successfully.")
            conn.commit()
            cursor.close()
            return True
        except pyodbc.Error as e:
            logging.error(f"Budgets API Database error: {e}")
            return False
    except Exception as e:
        logging.error(f"Budgets API Error: {e}")