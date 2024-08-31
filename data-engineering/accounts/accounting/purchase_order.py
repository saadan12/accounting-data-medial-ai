import pyodbc
import json
import logging
from accounts.accounting.insert_attachments import insert_attachments_data
from accounts.accounting.connection import format_date
from utilities import call_api,parse_datetime
    
def insert_purchase_orders_data(token,tenant, xero_userid, conn,user_id):
    try:
        cursor = conn.cursor()
        data = call_api(tenant, token,"PurchaseOrders")

        try:
            for order in data.get("PurchaseOrders", []):
                purchase_order_id = order.get("PurchaseOrderID", "")
                contactName = order.get("Contact", {}).get("Name", "")
                line_items = json.dumps(order.get("LineItems", []))
                UpdatedDateUTC = format_date(order.get("UpdatedDateUTC", ""))
                date = format_date(order.get("Date", ""))
                delivery_date = format_date(order.get("DeliveryDate", ""))
                purchase_order_number = order.get("PurchaseOrderNumber", "")
                reference = order.get("Reference", "")
                status = order.get("Status", "")
                delivery_addresses = order.get("DeliveryAddress", "")
                telephone = order.get("Telephone", "")
                delivery_instructions = order.get("DeliveryInstructions", "")
                expected_arrival_date = format_date(order.get("ExpectedArrivalDate", ""))
                sub_total = order.get("SubTotal", 0.0)
                total_tax = order.get("TotalTax", 0.0)
                total = order.get("Total", 0.0)
                has_attachment = order.get("HasAttachments", "")
                if has_attachment:
                    insert_attachments_data(token, tenant, xero_userid, conn, "PurchaseOrders", purchase_order_id)

                # Check if the purchase order already exists
                cursor.execute("SELECT COUNT(*) FROM PurchaseOrders WHERE PurchaseOrderID = ? AND user_id = ?", (purchase_order_id,user_id))
                result = cursor.fetchone()
                if result[0] == 0:  # If purchase order ID doesn't exist in the database
                    cursor.execute("""
                        INSERT INTO PurchaseOrders (PurchaseOrderID,Date,DeliveryDate, ExpectedArrivaldate, ContactName, LineItems,  PurchaseOrderNumber, Reference, Status, DeliveryAddresses, Telephone, DeliveryInstructions, SubTotal, TotalTax, Total, xero_userID,user_id,UpdatedDateUTC)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?,?,?,?, ?, ?, ?, ?, ?,?,?)
                    """, (purchase_order_id,date,delivery_date, expected_arrival_date, contactName, line_items,  purchase_order_number, reference, status, delivery_addresses, telephone, delivery_instructions, sub_total, total_tax, total, xero_userid,user_id,UpdatedDateUTC))
                    logging.info(f"Purchase order with ID {purchase_order_id} inserted successfully.")
                else:
                    cursor.execute("SELECT UpdatedDateUTC FROM PurchaseOrders WHERE PurchaseOrderID = ? AND user_id = ?", (purchase_order_id, user_id))
                    updated_date_utc_existing = cursor.fetchone()[0]
                    updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                    updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                    created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                    if updated_date_utc_dt == created_date_utc_existing_dt:
                        logging.info(f"Purchase order with ID {purchase_order_id} already exists in the database.")
                    else:
                        cursor.execute("""
                            UPDATE PurchaseOrders
                            SET Date = ?, DeliveryDate = ?, ExpectedArrivaldate = ?, ContactName = ?, LineItems = ?, PurchaseOrderNumber = ?, Reference = ?, Status = ?, DeliveryAddresses = ?, Telephone = ?, DeliveryInstructions = ?, SubTotal = ?, TotalTax = ?, Total = ?, xero_userID = ?, UpdatedDateUTC = ?
                            WHERE PurchaseOrderID = ? AND user_id = ?
                        """, (date, delivery_date, expected_arrival_date, contactName, line_items, purchase_order_number, reference, status, delivery_addresses, telephone, delivery_instructions, sub_total, total_tax, total, xero_userid, UpdatedDateUTC, purchase_order_id, user_id))
                        logging.info(f"Purchase order with ID {purchase_order_id} updated successfully.")
            conn.commit()
            cursor.close()
            return True
        except pyodbc.Error as e:
            logging.error(f"Purchase Order Database error: {e}")
            return False
    except Exception as e:
        logging.error(f"Purchase Order API Error: {e}")