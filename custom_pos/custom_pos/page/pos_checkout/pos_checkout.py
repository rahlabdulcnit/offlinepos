


import frappe
import json
# import flt

@frappe.whitelist()
def get_pos_data():
    """
    Fetch all initial data needed for the POS to start:
    - Active POS Items
    - Available POS Profiles
    - Available Modes of Payment
    """
    items = frappe.get_all(
        "POS Item",
        filters={"is_active": 1},
        fields=["item_code", "item_name", "standard_selling_rate"]
    )
    
    profiles = frappe.get_all(
        "POS Profile",
        fields=["name", "profile_name"]
    )
    
    payment_modes = frappe.get_all(
        "Custom Mode Of Payment",
        fields=["name","mode_name"]
    )
    # tables = frappe.get_all(
    #     "POS Table",
    #     fields=["name", "table_number", "status"]
    # )

    return {
        "items": items,
        "profiles": profiles,
        "payment_modes": payment_modes,
        # "tables": tables  # Add tables to the response
    }
@frappe.whitelist()
def get_shift_sales_total(shift_name):
    opening = frappe.get_value("POS  Shift", shift_name, "opening_amount")
    total_sales = frappe.db.get_value(
        "POS Invoice", 
        {"pos_shift": shift_name, "docstatus": 1}, 
        "sum(grand_total)"
    ) or 0
    return {"total_sales": total_sales, "opening_amount": opening}

# @frappe.whitelist()
# def submit_pos_invoice(cart_data, pos_profile, payments_data):
#     """
#     Creates a POS Invoice and one or more Payment Entries based on the submitted data.
#     It automatically links to the currently open shift for the selected profile.
#     """
#     try:
#         # Find the currently open shift for the selected POS Profile
#         active_shift = frappe.db.get_value(
#             "POS Shift",
#             filters={"pos_profile": pos_profile, "status": "Open"},
#             fieldname="name"
#         )

#         if not active_shift:
#             # If no open shift is found, stop and raise an error
#             frappe.throw(f"No open POS Shift found for profile: {frappe.db.get_value('POS Profile', pos_profile, 'profile_name')}")

#         cart = json.loads(cart_data)
#         payments = json.loads(payments_data)
        
#         # 1. Create the POS Invoice document
#         invoice = frappe.new_doc("POS Invoice")
#         invoice.pos_profile = pos_profile
#         invoice.pos_shift = active_shift
        
#         for item in cart:
#             invoice.append("items", {
#                 "item": item.get("item_code"),
#                 "qty": item.get("qty"),
#                 "rate": item.get("standard_selling_rate")
#             })
        
#         # Save and Submit the invoice
#         invoice.insert(ignore_permissions=True)
#         invoice.submit()
        
#         # 2. Create multiple Payment Entries against the invoice
#         for payment_detail in payments:
#             if not payment_detail.get("amount") or flt(payment_detail.get("amount")) <= 0:
#                 continue

#             payment_entry = frappe.new_doc("POS Payment Entry")
#             payment_entry.pos_invoice = invoice.name
#             payment_entry.mode_of_payment = payment_detail.get("mode")
#             payment_entry.amount = payment_detail.get("amount")
#             payment_entry.insert(ignore_permissions=True)
#             payment_entry.submit()
            
#         return {"status": "Success", "invoice_name": invoice.name}
    
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "POS Invoice Submission Error")
#         return {"status": "Error", "message": str(e)}

@frappe.whitelist()
def submit_pos_invoice(cart_data, pos_profile, payments_data):
    """
    Creates a POS Invoice and one or more Payment Entries based on the submitted data.
    It automatically links to the currently open shift for the selected profile.
    """
    try:
        # Use frappe.get_all for a more robust and clear query
        active_shifts = frappe.get_all(
            "POS  Shift",
            filters={
                "pos_profile": pos_profile, # This 'pos_profile' is the ID from JavaScript
                "status": "Open"
            },
            fields=["name"],
            limit=1 # We only need the first open shift
        )

        if not active_shifts:
            # If no open shift is found, get the display name for a better error message and throw
            profile_display_name = frappe.db.get_value("POS Profile", pos_profile, "profile_name")
            frappe.throw(f"No open POS Shift found for profile: {profile_display_name}")

        # Get the name of the shift from the list of results
        active_shift = active_shifts[0].name

        cart = json.loads(cart_data)
        payments = json.loads(payments_data)
        
        # 1. Create the POS Invoice document
        invoice = frappe.new_doc("POS Invoice")
        invoice.pos_profile = pos_profile
        invoice.pos_shift = active_shift


        #  # Add the new fields
        # invoice.order_type = order_type
        # if order_type == 'Dine-In' and pos_table:
        #     invoice.pos_table = pos_table
        
        for item in cart:
            invoice.append("items", {
                "item": item.get("item_code"),
                "qty": item.get("qty"),
                "rate": item.get("standard_selling_rate")
            })
        
        # Save and Submit the invoice
        invoice.insert(ignore_permissions=True)
        invoice.submit()
        
        # 2. Create multiple Payment Entries against the invoice
        for payment_detail in payments:
            if not payment_detail.get("amount") or float(payment_detail.get("amount")) <= 0:
                continue

            payment_entry = frappe.new_doc("POS Payment Entry")
            payment_entry.pos_invoice = invoice.name
            payment_entry.mode_of_payment = payment_detail.get("mode")
            payment_entry.amount = payment_detail.get("amount")
            payment_entry.insert(ignore_permissions=True)
            payment_entry.submit()

            # # After submitting the invoice, update the table status to 'Occupied'
            # if order_type == 'Dine-In' and pos_table:
            #    frappe.db.set_value("POS Table", pos_table, "status", "Occupied")
            
        return {"status": "Success", "invoice_name": invoice.name,"print_url": f"/printview?doctype=POS Invoice&name={invoice.name}&format=Receipt&no_letterhead=1"}
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "POS Invoice Submission Error")
        return {"status": "Error", "message": str(e)}


# THIS IS THE FINAL AND MOST ROBUST VERSION
# @frappe.whitelist()
# def submit_pos_invoice(cart_data, pos_profile, payments_data):
#     try:
#         # Step 1: Validate that we received a POS Profile ID from the frontend.
#         if not pos_profile:
#             frappe.throw("Critical Error: POS Profile ID was not received from the browser.")

#         # Step 2: Use a direct, failsafe SQL query to find the open shift.
#         # This bypasses the Frappe ORM which is causing the ('DocType', 'POS Shift') error.
#         # It directly queries the database table `tabPOS Shift`.
#         active_shift_result = frappe.db.sql("""
#             SELECT `name`
#             FROM `tabPOS Shift`
#             WHERE `pos_profile` = %(pos_profile)s
#             AND `status` = 'Open'
#             LIMIT 1
#         """, {"pos_profile": pos_profile}, as_dict=True)

#         # Step 3: Check if the query returned anything.
#         if not active_shift_result:
#             # If nothing was found, get the user-friendly name of the profile to show in the error.
#             profile_display_name = frappe.db.get_value("POS Profile", pos_profile, "profile_name")
#             frappe.throw(f"No open POS Shift could be found for the profile: '{profile_display_name}'. Please ensure a shift is open.")

#         # If a shift was found, get its name.
#         active_shift = active_shift_result[0].name

#         # --- The rest of the logic remains the same ---

#         cart = json.loads(cart_data)
#         payments = json.loads(payments_data)
        
#         invoice = frappe.new_doc("POS Invoice")
#         invoice.pos_profile = pos_profile
#         invoice.pos_shift = active_shift
        
#         for item in cart:
#             invoice.append("items", {
#                 "item": item.get("item_code"),
#                 "qty": item.get("qty"),
#                 "rate": item.get("rate")
#             })
        
#         invoice.insert(ignore_permissions=True)
#         invoice.submit()
        
#         for payment_detail in payments:
#             if not payment_detail.get("amount") or float(payment_detail.get("amount")) <= 0:
#                 continue
#             payment_entry = frappe.new_doc("POS Payment Entry")
#             payment_entry.pos_invoice = invoice.name
#             payment_entry.mode_of_payment = payment_detail.get("mode")
#             payment_entry.amount = payment_detail.get("amount")
#             payment_entry.insert(ignore_permissions=True)
#             payment_entry.submit()
            
#         return {"status": "Success", "invoice_name": invoice.name}
    
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "POS Invoice Submission Failed")
#         return {"status": "Error", "message": str(e)}