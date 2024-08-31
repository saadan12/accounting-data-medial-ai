import pyodbc
import logging
import time
from utilities import call_api

def get_employee_data(token, tenant, xero_userID, conn,user_id):
    try:
        cursor = conn.cursor()
        time.sleep(5)
        data = call_api(tenant, token,"Employee")
        # Insert employees into the database
        for employee in data.get("Employees", []):
            employee_id = employee.get("EmployeeID", "")
            status = employee.get("Status", "")
            first_name = employee.get("FirstName", "")
            last_name = employee.get("LastName", "")

            try:
                cursor.execute("SELECT COUNT(*) FROM Employee WHERE Employee_id = ? AND user_id = ?", (employee_id,user_id))
                result = cursor.fetchone()
                if result[0] == 0:  # If EmployeeID doesn't exist in the database
                    cursor.execute("""
                        INSERT INTO Employee (Employee_id, status, first_name, last_name, xero_userID,user_id)
                        VALUES (?, ?, ?, ?,?, ?)
                    """, (employee_id, status, first_name, last_name, xero_userID,user_id))
                    logging.info(f"Employee API Employee {first_name} {last_name} with ID {employee_id} inserted successfully.")
                else:
                    logging.info(f"Employee API Employee with ID {employee_id} already exists in the database.")
            except pyodbc.Error as e:
                logging.error(f"Employee API Database error: {e}")
                return False
        try:
            conn.commit()
            cursor.close()
        except pyodbc.Error as e:
            logging.error(f"Employee API DB Commit error: {e}")
            return False
        return True
    except Exception as e:
        logging.error(f"Employee API Error: {e}")
