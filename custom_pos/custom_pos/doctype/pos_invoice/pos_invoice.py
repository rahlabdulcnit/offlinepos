# Copyright (c) 2025, Hayrunnisa and contributors
# For license information, please see license.txt


# 

# # custom_pos/custom_pos/doctype/pos_invoice/pos_invoice.py

# import frappe
# from frappe.model.document import Document
# from frappe.utils import flt

# class POSInvoice(Document):
#     # --- Existing methods like validate, calculate_totals, etc. ---
#     def validate(self):
#         self.calculate_totals()
#         self.calculate_paid_amount()
#         self.update_invoice_status()
#         # Note: We will handle table status updates in on_submit and on_update/on_trash
#         # to ensure they happen at the correct stage of the document lifecycle.

#     # ... (your existing calculate_totals, calculate_paid_amount, update_invoice_status methods) ...
#     # Ensure these methods are present from previous steps.


#     # --- New methods for Table Status Logic ---

#     def on_submit(self):
#         """
#         Called when the POS Invoice is submitted (docstatus changes from 0 to 1).
#         """
#         self.update_table_status_on_submit()
#         # You might have other on_submit logic here too.

#     def on_update_after_submit(self):
#         """
#         Called when a SUBMITTED POS Invoice is updated (e.g., payment applied, status changes).
#         The 'on_update' hook runs for both new and updated documents.
#         'on_update_after_submit' specifically runs for updates to already submitted documents.
#         """
#         self.update_table_status_on_payment_or_cancellation()

#     def on_trash(self): # Or on_cancel if you prefer to hook into cancellation workflow explicitly
#         """
#         Called when the POS Invoice is cancelled (docstatus changes to 2) or deleted.
#         If using on_cancel, it's triggered when doc.cancel() is called.
#         on_trash is broader, covering deletion too. Let's assume cancellation sets docstatus=2.
#         If you only want to handle explicit cancellation (docstatus 2),
#         you might check self.docstatus == 2 within on_update_after_submit or a specific on_cancel hook.
#         For simplicity with your blueprint mentioning 'Cancelled' status, let's use on_update_after_submit
#         and check the invoice status field.
#         """
#         # We'll use the invoice's 'status' field in update_table_status_on_payment_or_cancellation
#         pass


#     def update_table_status_on_submit(self):
#         """
#         If it's a 'Dine-In' order and a table is linked, mark the table as 'Occupied'.
#         """
#         # Check if table_number is linked, order_type is 'Dine-In'
#         if self.table_number and self.order_type == "Dine-In":
#             try:
#                 table_doc = frappe.get_doc("POS Table", self.table_number)
#                 if table_doc.status != "Occupied":
#                     table_doc.status = "Occupied"
#                     table_doc.save(ignore_permissions=True) # ignore_permissions might be needed if run by a user without direct save rights on POS Table
#                     frappe.db.commit() # Ensure change is saved immediately
#                     frappe.msgprint(f"Table '{self.table_number}' status set to Occupied.")
#             except frappe.DoesNotExistError:
#                 frappe.log_error(f"POS Table '{self.table_number}' not found for POS Invoice '{self.name}'.", "Table Status Update Error")
#             except Exception as e:
#                 frappe.log_error(frappe.get_traceback(), f"Error updating POS Table '{self.table_number}' for POS Invoice '{self.name}'")

#     def update_table_status_on_payment_or_cancellation(self):
#         """
#         If the invoice was 'Dine-In', linked to a table, and is now 'Paid' or 'Cancelled',
#         mark the table as 'Free'.
#         """
#         # Ensure this invoice was a Dine-In and had a table linked.
#         # We also need to ensure we don't accidentally free a table
#         # that might have been occupied by a *new* invoice for the same table.
#         # This logic assumes one active invoice per table for 'Occupied' status.

#         # We get the original document's state before the update using get_doc_before_save
#         # However, for 'status' changes, self.status will reflect the new status.

#         if self.table_number and self.get("order_type") == "Dine-In": # Check original order_type if it could change
#             if self.status == "Paid" or self.status == "Cancelled":
#                 try:
#                     # Check if there are other active (Submitted, not Paid, not Cancelled)
#                     # 'Dine-In' invoices for the same table.
#                     other_active_invoices_for_table = frappe.db.exists(
#                         "POS Invoice",
#                         {
#                             "table_number": self.table_number,
#                             "order_type": "Dine-In",
#                             "name": ["!=", self.name], # Exclude the current invoice
#                             "status": ["not in", ["Paid", "Cancelled", "Draft"]], # Submitted but not yet resolved
#                             "docstatus": 1 # Submitted
#                         }
#                     )

#                     if not other_active_invoices_for_table:
#                         # No other active invoices for this table, so we can free it.
#                         table_doc = frappe.get_doc("POS Table", self.table_number)
#                         if table_doc.status != "Free":
#                             table_doc.status = "Free"
#                             table_doc.save(ignore_permissions=True)
#                             frappe.db.commit()
#                             frappe.msgprint(f"Table '{self.table_number}' status set to Free.")
#                     else:
#                         frappe.msgprint(f"Table '{self.table_number}' is still occupied by another active invoice.")

#                 except frappe.DoesNotExistError:
#                     frappe.log_error(f"POS Table '{self.table_number}' not found when trying to free for POS Invoice '{self.name}'.", "Table Status Update Error")
#                 except Exception as e:
#                     frappe.log_error(frappe.get_traceback(), f"Error freeing POS Table '{self.table_number}' for POS Invoice '{self.name}'")

#     # Make sure you have your other methods like calculate_totals, calculate_paid_amount, update_invoice_status
#     # For example:
#     def calculate_totals(self):
#         self.subtotal = 0
#         if self.items:
#             for item_row in self.items:
#                 if item_row.qty and item_row.rate:
#                     item_row.amount = flt(item_row.qty) * flt(item_row.rate)
#                 else:
#                     item_row.amount = 0
#                 self.subtotal += flt(item_row.amount)
#         self.discount_amount = flt(self.discount_amount)
#         self.total_tax_amount = flt(self.total_tax_amount)
#         self.grand_total = flt(self.subtotal) - flt(self.discount_amount) + flt(self.total_tax_amount)

#     def calculate_paid_amount(self):
#         if not self.name:
#             self.paid_amount = 0
#             return
#         payment_entries = frappe.db.get_all(
#             "POS Payment Entry",
#             filters={"pos_invoice": self.name, "docstatus": 1},
#             fields=["amount"]
#         )
#         self.paid_amount = sum(flt(p.amount) for p in payment_entries)

#     def update_invoice_status(self):
#         if self.docstatus == 0:
#             self.status = "Draft"
#         elif self.docstatus == 1:
#             if flt(self.grand_total) > 0 and flt(self.paid_amount) >= flt(self.grand_total):
#                 self.status = "Paid"
#             else:
#                 self.status = "Submitted"
#         elif self.docstatus == 2:
#             self.status = "Cancelled"
#         else:
#             self.status = "Draft"



# Copyright (c) 2025, Hayrunnisa and contributors
# For license information, please see license.txt

# custom_pos/custom_pos/doctype/pos_invoice/pos_invoice.py

# Copyright (c) 2025, Hayrunnisa and contributors
# For license information, please see license.txt

# custom_pos/custom_pos/doctype/pos_invoice/pos_invoice.py

# import frappe
# from frappe.model.document import Document
# from frappe.utils import flt, get_datetime # Import get_datetime if needed for end_time

# class POSInvoice(Document):

#     def validate(self):
#         """
#         Called before save, and before submit.
#         Also called when an existing document is saved.
#         """
#         self.calculate_totals()
#         if self.name: # Only calculate paid amount if the document has been saved at least once
#             self.calculate_paid_amount()
#         self.update_invoice_status() # Sets custom status based on docstatus and paid_amount

#     def on_submit(self):
#         """
#         Called after successful first submission (docstatus 0 -> 1).
#         """
#         # Ensure paid_amount and status are fresh for a brand new submission
#         if self.name: # Should always have a name at this point
#              self.calculate_paid_amount()
#         self.update_invoice_status() # Re-confirm status

#         self.update_table_status_on_submit() # Occupy table

#     def on_update_after_submit(self):
#         """
#         Called when a submitted document (docstatus=1) is saved again.
#         The `validate` hook would have already run, updating paid_amount and status.
#         This hook is good for actions that depend on that updated status (e.g., becoming "Paid").
#         """
#         self.update_table_status_on_payment_or_cancellation() # Free table if Paid/Cancelled

#     def on_cancel(self):
#         """
#         Called after successful cancellation (docstatus 1 -> 2).
#         """
#         self.update_invoice_status() # This will set self.status to "Cancelled"
#         self.update_table_status_on_payment_or_cancellation() # Free table

#     # --- Table Status Logic ---
#     def update_table_status_on_submit(self):
#         if self.table_number and self.order_type == "Dine-In":
#             try:
#                 current_table_status = frappe.db.get_value("POS Table", self.table_number, "status")
#                 if current_table_status != "Occupied":
#                     frappe.db.set_value("POS Table", self.table_number, "status", "Occupied")
#                     frappe.msgprint(f"Table '{self.table_number}' status set to Occupied.")
#             except Exception as e:
#                 frappe.log_error(message=f"Error updating POS Table '{self.table_number}' to Occupied for Invoice {self.name}", title=f"Table Status Error: {e}")

#     def update_table_status_on_payment_or_cancellation(self):
#         if self.table_number and self.get("order_type") == "Dine-In": # Use self.get for original value if type could change
#             if self.status == "Paid" or self.status == "Cancelled":
#                 try:
#                     other_active_invoices_for_table = frappe.db.exists(
#                         "POS Invoice",
#                         {
#                             "table_number": self.table_number,
#                             "order_type": "Dine-In",
#                             "name": ["!=", self.name],
#                             "status": ["not in", ["Paid", "Cancelled", "Draft"]],
#                             "docstatus": 1
#                         }
#                     )
#                     if not other_active_invoices_for_table:
#                         current_table_status = frappe.db.get_value("POS Table", self.table_number, "status")
#                         if current_table_status != "Free":
#                             frappe.db.set_value("POS Table", self.table_number, "status", "Free")
#                             frappe.msgprint(f"Table '{self.table_number}' status set to Free.")
#                     else:
#                         frappe.msgprint(f"Table '{self.table_number}' is still occupied by another active invoice.")
#                 except Exception as e:
#                     frappe.log_error(message=f"Error updating POS Table '{self.table_number}' to Free for Invoice {self.name}", title=f"Table Status Error: {e}")

#     # --- Calculation and Status Helper Methods ---
#     def calculate_totals(self):
#         self.subtotal = 0
#         if self.items:
#             for item_row in self.items:
#                 item_row.amount = flt(item_row.qty) * flt(item_row.rate)
#                 self.subtotal += flt(item_row.amount)
#         self.discount_amount = flt(self.discount_amount)
#         self.total_tax_amount = flt(self.total_tax_amount)
#         self.grand_total = flt(self.subtotal) - flt(self.discount_amount) + flt(self.total_tax_amount)

#     def calculate_paid_amount(self):
#         if not self.name:
#             self.paid_amount = 0
#             return
#         payment_entries = frappe.db.get_all(
#             "POS Payment Entry",
#             filters={"pos_invoice": self.name, "docstatus": 1},
#             fields=["amount"]
#         )
#         self.paid_amount = sum(flt(p.get("amount", 0)) for p in payment_entries)
#         # frappe.msgprint(f"[{self.name}] Calculated paid_amount: {self.paid_amount}") # Debug

#     def update_invoice_status(self):
#         # original_status = self.status # Debug
#         if self.docstatus == 0:
#             self.status = "Draft"
#         elif self.docstatus == 1: # Submitted
#             if flt(self.grand_total) > 0 and flt(self.paid_amount) >= flt(self.grand_total):
#                 self.status = "Paid"
#             elif flt(self.grand_total) == 0: # Zero value invoice considered paid if submitted
#                  self.status = "Paid"
#             else:
#                 self.status = "Submitted" # Or "Unpaid"
#         elif self.docstatus == 2: # Cancelled
#             self.status = "Cancelled"
#         # if original_status != self.status: # Debug
#             # frappe.msgprint(f"[{self.name}] Status changed from '{original_status}' to '{self.status}'. Paid: {self.paid_amount}, Total: {self.grand_total}, DocStatus: {self.docstatus}")









# # custom_pos/custom_pos/doctype/pos_invoice/pos_invoice.py
# import frappe
# from frappe.model.document import Document
# from frappe.utils import flt

# class POSInvoice(Document):

#     def validate(self):
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] --- POSInvoice.validate() START ---</b><br>DocStatus: {self.docstatus}, Current Custom Status: {self.status or 'Not Set'}", title="Invoice Validate")
#         self.calculate_totals() # Ensure grand_total is set
#         if self.name:
#             self.calculate_paid_amount() # Crucial: Calculate paid amount
#         self.update_invoice_status() # Update custom status based on new paid_amount and grand_total
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] --- POSInvoice.validate() END ---</b><br>New Custom Status: {self.status}, Paid: {self.paid_amount}, Grand: {self.grand_total}", title="Invoice Validate End")

#     def on_submit(self):
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] --- POSInvoice.on_submit() START ---</b>", title="Invoice On Submit")
#         # Validate hook would have run just before this, so paid_amount and status should be set
#         # if it's a brand new submission.
#         # For clarity, let's ensure they are up-to-date for the submitted state.
#         if self.name:
#             self.calculate_paid_amount()
#         self.update_invoice_status()
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] POSInvoice.on_submit()</b><br>Custom Status after re-update: {self.status}, Paid: {self.paid_amount}", title="Invoice On Submit Status")
#         self.update_table_status_on_submit()
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] --- POSInvoice.on_submit() END ---</b>", title="Invoice On Submit End")

#     def on_update_after_submit(self):
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] --- POSInvoice.on_update_after_submit() START ---</b><br>Current Custom Status before table logic: {self.status}, Paid: {self.paid_amount}", title="Invoice Update After Submit")
#         # The validate() hook has ALREADY RUN because this is triggered by a .save() on a submitted doc.
#         # So, self.status should be the most up-to-date (e.g., "Paid" if applicable).
#         self.update_table_status_on_payment_or_cancellation()
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] --- POSInvoice.on_update_after_submit() END ---</b>", title="Invoice Update After Submit End")

#     def on_cancel(self):
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] --- POSInvoice.on_cancel() START ---</b>", title="Invoice On Cancel")
#         self.update_invoice_status() # This will set self.status to "Cancelled"
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] POSInvoice.on_cancel()</b><br>Custom Status after update: {self.status}", title="Invoice On Cancel Status")
#         self.update_table_status_on_payment_or_cancellation()
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] --- POSInvoice.on_cancel() END ---</b>", title="Invoice On Cancel End")

#     --- Table Status Logic (Assumed correct with frappe.db.set_value as per previous) ---
#     def update_table_status_on_submit(self):
#         # ... (your existing code using frappe.db.set_value) ...
#         if self.table_number and self.order_type == "Dine-In":
#             try:
#                 current_table_status = frappe.db.get_value("POS Table", self.table_number, "status")
#                 if current_table_status != "Occupied":
#                     frappe.db.set_value("POS Table", self.table_number, "status", "Occupied")
#                     frappe.msgprint(f"Table '{self.table_number}' status set to Occupied by invoice {self.name}.", title="Table Status Update")
#             except Exception as e:
#                 frappe.log_error(message=f"Error in update_table_status_on_submit for Invoice {self.name}", title=f"Table Status Error: {e}")




    





#     def update_table_status_on_payment_or_cancellation(self):
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] update_table_status_on_payment_or_cancellation</b><br>Checking conditions - Invoice Status: {self.status}, Order Type: {self.get('order_type')}", title="Table Free Check")
#         if self.table_number and self.get("order_type") == "Dine-In":
#             if self.status == "Paid" or self.status == "Cancelled":
#                 # ... (your existing logic to check other_active_invoices_for_table and then frappe.db.set_value to "Free") ...
#                 # Make sure to add msgprints inside this block too if it's not working
#                 frappe.msgprint(f"<b>DEBUG: [{self.name}] update_table_status_on_payment_or_cancellation</b><br>Condition MET: Invoice is Paid or Cancelled. Will attempt to free table.", title="Table Free Check")
#                 try:
#                     other_active_invoices_for_table = frappe.db.exists(
#                         "POS Invoice",
#                         {
#                             "table_number": self.table_number,
#                             "order_type": "Dine-In",
#                             "name": ["!=", self.name],
#                             "status": ["not in", ["Paid", "Cancelled", "Draft"]],
#                             "docstatus": 1
#                         }
#                     )
#                     if not other_active_invoices_for_table:
#                         current_table_status = frappe.db.get_value("POS Table", self.table_number, "status")
#                         if current_table_status != "Free":
#                             frappe.db.set_value("POS Table", self.table_number, "status", "Free")
#                             frappe.msgprint(f"Table '{self.table_number}' status set to Free by invoice {self.name}.", title="Table Status Update")
#                     else:
#                         frappe.msgprint(f"Table '{self.table_number}' is still occupied by another active invoice (checked by invoice {self.name}).", title="Table Status Update")
#                 except Exception as e:
#                     frappe.log_error(message=f"Error updating POS Table '{self.table_number}' to Free for Invoice {self.name}", title=f"Table Status Error: {e}")

#             else:
#                 frappe.msgprint(f"<b>DEBUG: [{self.name}] update_table_status_on_payment_or_cancellation</b><br>Condition NOT MET: Invoice Status is '{self.status}'. Table status not changed.", title="Table Free Check")


#     # --- Calculation and Status Helper Methods (with detailed msgprints) ---
#     def calculate_totals(self):
#         # No msgprint needed here unless grand_total is suspect
#         self.subtotal = 0
#         if self.items:
#             for item_row in self.items:
#                 item_row.amount = flt(item_row.qty) * flt(item_row.rate)
#                 self.subtotal += flt(item_row.amount)
#         self.discount_amount = flt(self.discount_amount)
#         self.total_tax_amount = flt(self.total_tax_amount)
#         self.grand_total = flt(self.subtotal) - flt(self.discount_amount) + flt(self.total_tax_amount)

#     def calculate_paid_amount(self):
#         if not self.name:
#             self.paid_amount = 0
#             return

#         payment_entries = frappe.db.get_all(
#             "POS Payment Entry",
#             filters={"pos_invoice": self.name, "docstatus": 1},
#             fields=["name", "amount"] # fetch name for debugging
#         )
#         current_sum = sum(flt(p.get("amount", 0)) for p in payment_entries)
#         frappe.msgprint(f"<b>DEBUG: [{self.name}] calculate_paid_amount</b><br>Fetched Payments: {payment_entries}<br>Calculated Sum: {current_sum}", title="Paid Amount Calc")
#         self.paid_amount = current_sum

#     def update_invoice_status(self):
#         original_custom_status = self.status
#         paid_amount_val = flt(self.paid_amount)
#         grand_total_val = flt(self.grand_total)

#         frappe.msgprint(f"<b>DEBUG: [{self.name}] update_invoice_status START</b><br>DocStatus: {self.docstatus}, PaidAmount: {paid_amount_val}, GrandTotal: {grand_total_val}, CurrentCustomStatus: {original_custom_status}", title="Update Invoice Status")

#         new_status = original_custom_status # Default to no change

#         if self.docstatus == 0:
#             new_status = "Draft"
#         elif self.docstatus == 1: # Submitted
#             if grand_total_val > 0 and paid_amount_val >= grand_total_val:
#                 new_status = "Paid"
#             elif grand_total_val == 0: # Zero value invoice
#                  new_status = "Paid"
#             else:
#                 new_status = "Submitted"
#         elif self.docstatus == 2: # Cancelled
#             new_status = "Cancelled"
        
#         self.status = new_status
#         if original_custom_status != self.status:
#             frappe.msgprint(f"<b>DEBUG: [{self.name}] update_invoice_status END</b><br>Custom Status CHANGED from '{original_custom_status}' to '{self.status}'", title="Update Invoice Status")
#         else:
#             frappe.msgprint(f"<b>DEBUG: [{self.name}] update_invoice_status END</b><br>Custom Status REMAINS '{self.status}' (was '{original_custom_status}')", title="Update Invoice Status")












# # custom_pos/custom_pos/doctype/pos_invoice/pos_invoice.py
# # Copyright (c) 2023, Your Name and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document
# from frappe.utils import flt # Ensure flt is imported

# class POSInvoice(Document):

#     def validate(self):
#         frappe.msgprint(
#             (
#                 f"<b>DEBUG: [{self.name}] --- POSInvoice.validate() START ---</b><br>"
#                 f"DocStatus: {self.docstatus}, Current Custom Status: {self.status or 'Not Set'}"
#             ),
#             title="Invoice Validate START"
#         )
#         self.calculate_totals()  # Ensure grand_total is set
#         if self.name: # Only calculate paid amount if the document has been saved at least once
#             self.calculate_paid_amount()  # Crucial: Calculate paid amount
#         self.update_invoice_status()  # Update custom status based on new paid_amount and grand_total
#         frappe.msgprint(
#             (
#                 f"<b>DEBUG: [{self.name}] --- POSInvoice.validate() END ---</b><br>"
#                 f"New Custom Status: {self.status}, Paid: {self.paid_amount}, Grand: {self.grand_total}"
#             ),
#             title="Invoice Validate END"
#         )

#     def on_submit(self):
#         frappe.msgprint(
#             f"<b>DEBUG: [{self.name}] --- POSInvoice.on_submit() START ---</b>",
#             title="Invoice On Submit START"
#         )
#         # validate() has already run just before this hook.
#         # For clarity, we can ensure paid_amount and status are re-evaluated if needed for this specific hook's logic.
#         if self.name:
#             self.calculate_paid_amount()
#         self.update_invoice_status()
#         frappe.msgprint(
#             (
#                 f"<b>DEBUG: [{self.name}] POSInvoice.on_submit()</b><br>"
#                 f"Custom Status after re-update: {self.status}, Paid: {self.paid_amount}"
#             ),
#             title="Invoice On Submit - Status Check"
#         )
#         self.update_table_status_on_submit() # This marks table as Occupied
#         frappe.msgprint(
#             f"<b>DEBUG: [{self.name}] --- POSInvoice.on_submit() END ---</b>",
#             title="Invoice On Submit END"
#         )

#     def on_update_after_submit(self):
#         frappe.msgprint(
#             (
#                 f"<b>DEBUG: [{self.name}] --- POSInvoice.on_update_after_submit() START ---</b><br>"
#                 f"Current Custom Status when hook starts: {self.status}, Paid Amount: {self.paid_amount}"
#             ),
#             title="Invoice Update After Submit START"
#         )
#         # The validate() hook has ALREADY RUN because this is triggered by a .save() on a submitted doc.
#         # So, self.status (custom status) should be the most up-to-date.
#         self.update_table_status_on_payment_or_cancellation() # This attempts to free the table
#         frappe.msgprint(
#             f"<b>DEBUG: [{self.name}] --- POSInvoice.on_update_after_submit() END ---</b>",
#             title="Invoice Update After Submit END"
#         )

#     def on_cancel(self):
#         frappe.msgprint(
#             f"<b>DEBUG: [{self.name}] --- POSInvoice.on_cancel() START ---</b>",
#             title="Invoice On Cancel START"
#         )
#         self.update_invoice_status()  # This will set self.status to "Cancelled"
#         frappe.msgprint(
#             (
#                 f"<b>DEBUG: [{self.name}] POSInvoice.on_cancel()</b><br>"
#                 f"Custom Status after update_invoice_status: {self.status}"
#             ),
#             title="Invoice On Cancel - Status Check"
#         )
#         self.update_table_status_on_payment_or_cancellation() # This attempts to free the table
#         frappe.msgprint(
#             f"<b>DEBUG: [{self.name}] --- POSInvoice.on_cancel() END ---</b>",
#             title="Invoice On Cancel END"
#         )

#     # --- Table Status Logic methods ---
#     def update_table_status_on_submit(self):
#         frappe.msgprint(
#             f"<b>DEBUG: [{self.name}] update_table_status_on_submit CALLED</b><br>"
#             f"Order Type: {self.order_type}, Table: {self.table_number}",
#             title="Table Occupy Check"
#         )
#         if self.table_number and self.order_type == "Dine-In":
#             try:
#                 current_table_status = frappe.db.get_value("POS Table", self.table_number, "status")
#                 if current_table_status != "Occupied":
#                     frappe.db.set_value("POS Table", self.table_number, "status", "Occupied")
#                     frappe.msgprint(f"Table '{self.table_number}' status successfully set to Occupied by invoice {self.name}.", title="Table Status Update SUCCESS")
#                 else:
#                     frappe.msgprint(f"Table '{self.table_number}' was already Occupied (checked by {self.name}). No change made.", title="Table Status Info - Already Occupied")
#             except Exception as e:
#                 frappe.log_error(message=frappe.get_traceback(), title=f"Error in update_table_status_on_submit for Invoice {self.name} (Table: {self.table_number})")
#                 frappe.msgprint(f"<b>ERROR: [{self.name}] An error occurred trying to set table '{self.table_number}' to Occupied. Check server logs.</b><br>Error: {str(e)}", title="Table Update Script Error", indicator="red")

#     def update_table_status_on_payment_or_cancellation(self):
#         frappe.msgprint(
#             (
#                 f"<b>DEBUG: [{self.name}] update_table_status_on_payment_or_cancellation CALLED</b><br>"
#                 f"Checking conditions - Invoice Custom Status: {self.status}, Order Type: {self.get('order_type')}, Table: {self.table_number}"
#             ),
#             title="Table Free Check START"
#         )

#         if self.table_number and self.get("order_type") == "Dine-In":
#             if self.status == "Paid" or self.status == "Cancelled":
#                 frappe.msgprint(
#                     f"<b>DEBUG: [{self.name}] Condition MET: Invoice is '{self.status}'. Will check for other active invoices on table '{self.table_number}'.</b>",
#                     title="Table Free Check - Condition Met"
#                 )
#                 try:
#                     other_active_invoices_for_table = frappe.db.exists(
#                         "POS Invoice",
#                         {
#                             "table_number": self.table_number,
#                             "order_type": "Dine-In",
#                             "name": ["!=", self.name],  # Exclude the current invoice itself
#                             "status": ["not in", ["Paid", "Cancelled", "Draft"]],  # Check your custom status values
#                             "docstatus": 1  # Must be a submitted document
#                         }
#                     )
                    
#                     frappe.msgprint(
#                         f"<b>DEBUG: [{self.name}] Query for other active invoices on table '{self.table_number}'</b><br>"
#                         f"Result (frappe.db.exists found other active invoices?): {other_active_invoices_for_table}",
#                         title="Other Active Invoices Query Result"
#                     )

#                     if not other_active_invoices_for_table:
#                         # No other active invoices found for this table
#                         current_table_status_before_free = frappe.db.get_value("POS Table", self.table_number, "status")
#                         frappe.msgprint(
#                             f"<b>DEBUG: [{self.name}] No other active invoices found for table '{self.table_number}'.</b><br>"
#                             f"Current table status is '{current_table_status_before_free}'. Will set to 'Free'.",
#                             title="Table Freeing Logic - Proceeding"
#                         )
#                         if current_table_status_before_free != "Free":
#                             frappe.db.set_value("POS Table", self.table_number, "status", "Free")
#                             frappe.msgprint(f"Table '{self.table_number}' status successfully set to Free by invoice {self.name}.", title="Table Status Update SUCCESS")
#                         else:
#                             frappe.msgprint(f"Table '{self.table_number}' was already Free (checked by {self.name}). No change made.", title="Table Status Info - Already Free")
#                     else:
#                         # This invoice is Paid/Cancelled, but other invoices still keep the table occupied.
#                         frappe.msgprint(
#                             f"Table '{self.table_number}' is STILL OCCUPIED by another active invoice (Found: {other_active_invoices_for_table}). Checked by invoice {self.name}. Table status not changed to 'Free'.",
#                             title="Table Status Info - Still Occupied by Others"
#                         )
#                 except Exception as e:
#                     frappe.log_error(message=frappe.get_traceback(), title=f"Error in logic for updating POS Table '{self.table_number}' to Free for Invoice {self.name}: {e}")
#                     frappe.msgprint(f"<b>ERROR: [{self.name}] An error occurred trying to update table '{self.table_number}' status. Check server logs.</b><br>Error: {str(e)}", title="Table Update Script Error", indicator="red")
#             else:
#                 frappe.msgprint(
#                     f"<b>DEBUG: [{self.name}] Condition NOT MET: Invoice Status is '{self.status}' (not 'Paid' or 'Cancelled'). Table status not changed.</b>",
#                     title="Table Free Check - Condition NOT Met"
#                 )
#         else:
#             if not self.table_number:
#                 frappe.msgprint(f"<b>DEBUG: [{self.name}] No table number linked to this invoice. Table status logic skipped.</b>", title="Table Free Check - No Table")
#             if self.get("order_type") != "Dine-In": # Check original order_type if it could have changed
#                  frappe.msgprint(f"<b>DEBUG: [{self.name}] Order type is '{self.get('order_type')}' (not 'Dine-In'). Table status logic skipped.</b>", title="Table Free Check - Not DineIn")


#     # --- Calculation and Status Helper Methods ---
#     def calculate_totals(self):
#         self.subtotal = 0
#         if self.items:
#             for item_row in self.items:
#                 item_row.amount = flt(item_row.qty) * flt(item_row.rate)
#                 self.subtotal += flt(item_row.amount)
#         self.discount_amount = flt(self.discount_amount)
#         self.total_tax_amount = flt(self.total_tax_amount)
#         self.grand_total = flt(self.subtotal) - flt(self.discount_amount) + flt(self.total_tax_amount)
#         # Optional: msgprint for grand_total if needed for deep debugging totals
#         # frappe.msgprint(f"DEBUG: [{self.name}] calculate_totals - Grand Total: {self.grand_total}", title="Totals Calculation")


#     def calculate_paid_amount(self):
#         if not self.name:  # Document not saved yet, so no linked payments possible
#             self.paid_amount = 0
#             return

#         payment_entries = frappe.db.get_all(
#             "POS Payment Entry",
#             filters={"pos_invoice": self.name, "docstatus": 1},
#             fields=["name", "amount"]  # Fetch name for debugging
#         )
#         current_sum = sum(flt(p.get("amount", 0)) for p in payment_entries)
#         frappe.msgprint(
#             (
#                 f"<b>DEBUG: [{self.name}] calculate_paid_amount</b><br>"
#                 f"Fetched Payments: {payment_entries}<br>"
#                 f"Calculated Sum: {current_sum}"
#             ),
#             title="Paid Amount Calculation"
#         )
#         self.paid_amount = current_sum

#     def update_invoice_status(self):
#         original_custom_status = self.status
#         paid_amount_val = flt(self.paid_amount)
#         grand_total_val = flt(self.grand_total)

#         frappe.msgprint(
#             (
#                 f"<b>DEBUG: [{self.name}] update_invoice_status START</b><br>"
#                 f"DocStatus: {self.docstatus}, PaidAmount: {paid_amount_val}, GrandTotal: {grand_total_val}, CurrentCustomStatus: {original_custom_status or 'Not Set'}"
#             ),
#             title="Update Invoice Status - START"
#         )

#         new_status = original_custom_status  # Default to no change

#         if self.docstatus == 0:
#             new_status = "Draft"
#         elif self.docstatus == 1:  # Submitted
#             if grand_total_val > 0 and paid_amount_val >= grand_total_val:
#                 new_status = "Paid"
#             elif grand_total_val == 0:  # Zero value invoice considered paid if submitted
#                 new_status = "Paid"
#             else:
#                 new_status = "Submitted" # Or "Unpaid" if you prefer that term
#         elif self.docstatus == 2:  # Cancelled
#             new_status = "Cancelled"
        
#         self.status = new_status
#         if original_custom_status != self.status:
#             frappe.msgprint(
#                 f"<b>DEBUG: [{self.name}] update_invoice_status END</b><br>"
#                 f"Custom Status CHANGED from '{original_custom_status or 'Not Set'}' to '{self.status}'",
#                 title="Update Invoice Status - CHANGED"
#             )
#         else:
#             frappe.msgprint(
#                 f"<b>DEBUG: [{self.name}] update_invoice_status END</b><br>"
#                 f"Custom Status REMAINS '{self.status}' (was '{original_custom_status or 'Not Set'}')",
#                 title="Update Invoice Status - REMAINS"
#             )





# custom_pos/custom_pos/doctype/pos_invoice/pos_invoice.py
# Copyright (c) 2023, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt # Ensure flt is imported

class POSInvoice(Document):

    def validate(self):
        self.calculate_totals()
        if self.name: # Only calculate paid amount if the document has been saved at least once
            self.calculate_paid_amount()
        self.update_invoice_status() # Sets custom status based on docstatus and paid_amount

    def on_submit(self):
        # validate() has already run. Re-calculate/update status to be sure before table logic.
        if self.name:
            self.calculate_paid_amount()
        self.update_invoice_status()
        self.update_table_status_on_submit() # This marks table as Occupied

    def on_update_after_submit(self):
        # The validate() hook has ALREADY RUN because this is triggered by a .save() on a submitted doc.
        # So, self.status (custom status) should be the most up-to-date.
        self.update_table_status_on_payment_or_cancellation() # This attempts to free the table

    def on_cancel(self):
        self.update_invoice_status()  # This will set self.status to "Cancelled"
        self.update_table_status_on_payment_or_cancellation() # This attempts to free the table

    # --- Table Status Logic methods ---
    def update_table_status_on_submit(self):
        if self.table_number and self.order_type == "Dine-In":
            try:
                current_table_status = frappe.db.get_value("POS Table", self.table_number, "status")
                if current_table_status != "Occupied":
                    frappe.db.set_value("POS Table", self.table_number, "status", "Occupied")
                    # Optional: frappe.msgprint(f"Table '{self.table_number}' status set to Occupied.", title="Info")
            except Exception as e:
                frappe.log_error(message=frappe.get_traceback(), title=f"Error in update_table_status_on_submit for Invoice {self.name} (Table: {self.table_number})")

    def update_table_status_on_payment_or_cancellation(self):
        if self.table_number and self.get("order_type") == "Dine-In": # Use self.get for robustness if order_type could change
            if self.status == "Paid" or self.status == "Cancelled":
                try:
                    other_active_invoices_for_table = frappe.db.exists(
                        "POS Invoice",
                        {
                            "table_number": self.table_number,
                            "order_type": "Dine-In",
                            "name": ["!=", self.name],  # Exclude the current invoice itself
                            "status": ["not in", ["Paid", "Cancelled", "Draft"]],  # Check your custom status values
                            "docstatus": 1  # Must be a submitted document
                        }
                    )
                    
                    if not other_active_invoices_for_table:
                        # No other active invoices found for this table
                        current_table_status_before_free = frappe.db.get_value("POS Table", self.table_number, "status")
                        if current_table_status_before_free != "Free":
                            frappe.db.set_value("POS Table", self.table_number, "status", "Free")
                            # Optional: frappe.msgprint(f"Table '{self.table_number}' status set to Free.", title="Info")
                    # else:
                        # Optional: frappe.msgprint(f"Table '{self.table_number}' still occupied by other invoices.", title="Info")
                except Exception as e:
                    frappe.log_error(message=frappe.get_traceback(), title=f"Error in logic for updating POS Table '{self.table_number}' to Free for Invoice {self.name}: {e}")

    # --- Calculation and Status Helper Methods ---
    def calculate_totals(self):
        self.subtotal = 0
        if self.items:
            for item_row in self.items:
                item_row.amount = flt(item_row.qty) * flt(item_row.rate) # Ensure qty and rate exist and are numbers
                self.subtotal += flt(item_row.amount)
        self.discount_amount = flt(self.discount_amount) # Ensure these are numbers
        self.total_tax_amount = flt(self.total_tax_amount)
        self.grand_total = flt(self.subtotal) - flt(self.discount_amount) + flt(self.total_tax_amount)

    def calculate_paid_amount(self):
        if not self.name:  # Document not saved yet, so no linked payments possible
            self.paid_amount = 0
            return

        payment_entries = frappe.db.get_all(
            "POS Payment Entry",
            filters={"pos_invoice": self.name, "docstatus": 1}, # Only submitted payments
            fields=["amount"]
        )
        self.paid_amount = sum(flt(p.get("amount", 0)) for p in payment_entries) # Use .get for safety

    def update_invoice_status(self):
        paid_amount_val = flt(self.paid_amount)
        grand_total_val = flt(self.grand_total)
        new_status = self.status # Default to current status

        if self.docstatus == 0:
            new_status = "Draft"
        elif self.docstatus == 1:  # Submitted
            if grand_total_val > 0 and paid_amount_val >= grand_total_val:
                new_status = "Paid"
            elif grand_total_val == 0:  # Zero value invoice considered paid if submitted
                new_status = "Paid"
            else:
                new_status = "Submitted" # Or "Unpaid" if you prefer that term
        elif self.docstatus == 2:  # Cancelled
            new_status = "Cancelled"
        
        if self.status != new_status: # Only update if status actually changes
            self.status = new_status


