import pyodbc
import json
import logging
from .connection import format_date
from utilities import call_api,parse_datetime

def insert_items_data(token, tenant, xero_userID, conn,user_id):
    try:
        cursor = conn.cursor()
        data = call_api(tenant, token,"Items")

        try:
            for item in data.get("Items", []):
                item_id = item.get("ItemID", "")
                code = item.get("Code", "")
                inventory_asset_account_code = item.get("InventoryAssetAccountCode", None)  # Use None if not provided
                name = item.get("Name", "")
                UpdatedDateUTC = format_date(item.get("UpdatedDateUTC", ""))
                description = item.get("Description", "")
                purchase_details = json.dumps(item.get("PurchaseDetails", {}))
                UnitPrice = item.get("PurchaseDetails", {}).get("UnitPrice", "")
                # Ensure numeric fields are handled correctly
                total_cost_pool = item.get("TotalCostPool")
                total_cost_pool = float(total_cost_pool) if total_cost_pool else None
                
                quantity_on_hand = item.get("QuantityOnHand")
                quantity_on_hand = int(quantity_on_hand) if quantity_on_hand else None

                # Check if the item already exists
                cursor.execute("SELECT COUNT(*) FROM Items WHERE ItemID = ? AND user_id = ?", (item_id,user_id))
                result = cursor.fetchone()

                if result[0] == 0:  # If item ID doesn't exist in the database
                    cursor.execute("""

                        INSERT INTO Items (ItemID, Code, InventoryAssetAccountCode, Name, Description, PurchaseDetails, TotalCostPool, QuantityOnHand, xero_userID,user_id,UnitPrice,UpdatedDateUTC)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?)
                    """, (item_id, code, inventory_asset_account_code, name, description, purchase_details, total_cost_pool, quantity_on_hand, xero_userID,user_id,UnitPrice,UpdatedDateUTC))
                    logging.info(f"Items API Item with ID {item_id} inserted successfully.")
                else:
                    cursor.execute("SELECT UpdatedDateUTC FROM Items WHERE ItemID = ? AND user_id = ?", (item_id, user_id))
                    updated_date_utc_existing = cursor.fetchone()[0]
                    updated_date_utc_existing_str = updated_date_utc_existing.strftime("%Y-%m-%d %H:%M:%S")
                    updated_date_utc_dt = parse_datetime(UpdatedDateUTC)
                    created_date_utc_existing_dt = parse_datetime(updated_date_utc_existing_str)  # Parse as string
                    if updated_date_utc_dt == created_date_utc_existing_dt:
                        logging.info(f"Items API Item with ID {item_id} already exists in the database.")
                    else:
                        cursor.execute("""
                            UPDATE Items
                            SET Code = ?, InventoryAssetAccountCode = ?, Name = ?, Description = ?, PurchaseDetails = ?, TotalCostPool = ?,
                                QuantityOnHand = ?, xero_userID = ?, UpdatedDateUTC = ?, UnitPrice = ?
                            WHERE ItemID = ? AND user_id = ?
                        """, (code, inventory_asset_account_code, name, description, purchase_details, total_cost_pool,
                            quantity_on_hand, xero_userID, UpdatedDateUTC, UnitPrice, item_id, user_id))
                        logging.info(f"Items API Item with ID {item_id} updated successfully.")
            conn.commit()
            cursor.close()
            return True
        except pyodbc.Error as e:
            logging.error(f"Items API  Database error: {e}")
            return False
    except Exception as e:
        logging.error(f"Items API Error: {e}")