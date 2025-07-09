# Copyright (c) 2025, Hayrunnisa and contributors
# For license information, please see license.txt

#import frappe
# from frappe.model.document import Document

# class POSPaymentEntry(Document):
#     pass


# # custom_pos/custom_pos/doctype/pos_payment_entry/pos_payment_entry.py
# import frappe
# from frappe.model.document import Document

# class POSPaymentEntry(Document):
#     def on_submit(self):
#         if self.pos_invoice:
#             try:
#                 invoice_doc = frappe.get_doc("POS Invoice", self.pos_invoice)
#                 # Calling .save() on invoice_doc will trigger its .validate() hook,
#                 # then its .on_update_after_submit() hook if it was already submitted.
#                 invoice_doc.save(ignore_permissions=True) # ignore_permissions if payment user role != invoice save role
#                 frappe.db.commit() # Ensures invoice changes are saved before any further logic might depend on them.
#                 # frappe.msgprint(f"POS Invoice {invoice_doc.name} re-validated and saved after payment {self.name}.")
#             except Exception as e:
#                 frappe.log_error(message=f"Error re-validating POS Invoice {self.pos_invoice} after payment {self.name}", title=f"Invoice Update Error: {e}")






# # custom_pos/custom_pos/doctype/pos_payment_entry/pos_payment_entry.py
# import frappe
# from frappe.model.document import Document

# class POSPaymentEntry(Document):
#     def on_submit(self):
#         frappe.msgprint(f"<b>DEBUG: --- POSPaymentEntry.on_submit() START for {self.name} ---</b><br>Invoice: {self.pos_invoice}, Amount: {self.amount}", title="Payment Entry Submit")
#         if self.pos_invoice:
#             try:
#                 invoice_doc = frappe.get_doc("POS Invoice", self.pos_invoice)
#                 frappe.msgprint(f"<b>DEBUG: [{self.name}] Got invoice_doc {invoice_doc.name} (Current Status: {invoice_doc.status}, Paid: {invoice_doc.paid_amount}). Attempting to save it.</b>", title="Payment Entry Update Invoice")
                
#                 # Critical: This save should trigger POSInvoice.validate()
#                 invoice_doc.save(ignore_permissions=True) 
#                 frappe.db.commit() # Make sure invoice changes are committed

#                 # Fetch the invoice again to see its state *after* the save
#                 updated_invoice_doc = frappe.get_doc("POS Invoice", self.pos_invoice)
#                 frappe.msgprint(f"<b>DEBUG: [{self.name}] POS Invoice {updated_invoice_doc.name} state AFTER save.</b><br>New Custom Status: {updated_invoice_doc.status}, New Paid Amount: {updated_invoice_doc.paid_amount}", title="Payment Entry Invoice Updated")
#             except Exception as e:
#                 frappe.msgprint(f"<b>DEBUG: [{self.name}] ERROR re-validating POS Invoice {self.pos_invoice}.</b><br>Error: {e}", title="Payment Entry Error")
#                 frappe.log_error(message=f"Error re-validating POS Invoice {self.pos_invoice} after payment {self.name}", title=f"Invoice Update Error: {e}")
#         else:
#             frappe.msgprint(f"<b>DEBUG: [{self.name}] No POS Invoice linked to this payment entry.</b>", title="Payment Entry Info")
#         frappe.msgprint(f"<b>DEBUG: --- POSPaymentEntry.on_submit() END for {self.name} ---</b>", title="Payment Entry Submit End")



# custom_pos/custom_pos/doctype/pos_payment_entry/pos_payment_entry..name} ---</b><br>Invoice: {self.pos_invoice}, Amount: {self.amount}", title="py




# # custom_pos/custom_pos/doctype/pos_payment_entry/pos_payment_entry.py
# # Copyright (c) 2023, Your Name and contributors
# # For license information, please see license.txt

# import frappe
# from frappe.model.document import Document

# class POSPaymentEntry(Document):
#     def on_submit(self):
#         # Debug: Indicate start of the method
#         frappe.msgprint(
#             (
#                 f"<b>DEBUG: --- POSPaymentEntry.on_submit() START for {self.name} ---</b><br>"
#                 f"Invoice: {self.pos_invoice}, Amount: {self.amount}"
#             ),
#             title="Payment Entry: Submit START"
#         )

#         if self.pos_invoice:
#             invoice_doc_for_debug = None  # For debugging after save
#             try:
#                 # Fetch the document fresh to ensure we have the latest DB state
#                 invoice_doc = frappe.get_doc("POS Invoice", self.pos_invoice)
                
#                 frappe.msgprint(
#                     (
#                         f"<b>DEBUG: [{self.name}] Got invoice_doc {invoice_doc.name}</b><br>"
#                         f"Current DB Status: {invoice_doc.status}, Current DB Paid: {invoice_doc.paid_amount}.<br>"
#                         f"Calling its validate() & save() methods now."
#                     ),
#                     title=f"Payment Entry: Pre-Validate Invoice"
#                 )

#                 # 1. Explicitly call validate on the invoice document
#                 # This should update paid_amount and status in the invoice_doc object (in memory)
#                 invoice_doc.validate() 
                
#                 frappe.msgprint(
#                     (
#                         f"<b>DEBUG: [{self.name}] After invoice_doc.validate() was called for {invoice_doc.name}</b><br>"
#                         f"Invoice object's (in-memory) Status is now: {invoice_doc.status}<br>"
#                         f"Invoice object's (in-memory) Paid Amount is now: {invoice_doc.paid_amount}"
#                     ),
#                     title=f"Payment Entry: Invoice Post-Validate (In-Memory)"
#                 )

#                 # 2. Now save the invoice document with its (hopefully) updated values
#                 invoice_doc.save(ignore_permissions=True)
#                 frappe.db.commit()  # Ensure changes to POS Invoice are committed

#                 # For robust debugging, re-fetch the invoice to see what's actually in the DB
#                 invoice_doc_for_debug = frappe.get_doc("POS Invoice", self.pos_invoice)
#                 frappe.msgprint(
#                     (
#                         f"<b>DEBUG: [{self.name}] POS Invoice {invoice_doc_for_debug.name} state AFTER being saved.</b><br>"
#                         f"Status in DB: {invoice_doc_for_debug.status}<br>"
#                         f"Paid Amount in DB: {invoice_doc_for_debug.paid_amount}"
#                     ),
#                     title=f"Payment Entry: Invoice Updated in DB"
#                 )

#             except Exception as e:
#                 # Log the full traceback for server-side diagnosis
#                 frappe.log_error(
#                     message=frappe.get_traceback(),
#                     title=f"Error processing POS Invoice {self.pos_invoice} from POSPaymentEntry {self.name}"
#                 )
#                 # Show a user-friendly message and the specific error
#                 frappe.msgprint(
#                     (
#                         f"<b>DEBUG: [{self.name}] ERROR processing POS Invoice {self.pos_invoice}.</b><br>"
#                         f"<b>Error Type: {type(e).__name__}</b><br>"
#                         f"<b>Error Details: {str(e)}</b><br>"
#                         f"Check server error logs (frappe-bench/logs/error.log) for full traceback."
#                     ),
#                     title=f"Payment Entry: INVOICE PROCESSING FAILED",
#                     indicator='red'
#                 )
#         else:
#             frappe.msgprint(
#                 f"<b>DEBUG: [{self.name}] No POS Invoice linked to this payment entry.</b>",
#                 title=f"Payment Entry: Info for {self.name}"
#             )

#         # Debug: Indicate end of the method
#         frappe.msgprint(
#             f"<b>DEBUG: --- POSPaymentEntry.on_submit() END for {self.name} ---</b>",
#             title="Payment Entry: Submit END"
#         )









# custom_pos/custom_pos/doctype/pos_payment_entry/pos_payment_entry.py
# Copyright (c) 2023, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class POSPaymentEntry(Document):
    def on_submit(self):
        if self.pos_invoice:
            invoice_doc_to_update = None # Initialize to avoid issues if get_doc fails
            try:
                # Fetch the document fresh to ensure we are working with the latest DB state
                # before our script makes in-memory modifications to it.
                invoice_doc_to_update = frappe.get_doc("POS Invoice", self.pos_invoice)
                
                # 1. Explicitly call validate() on the POS Invoice document.
                # This is crucial because POSInvoice.validate() contains the logic to:
                #    - self.calculate_paid_amount() (which will now include this payment)
                #    - self.update_invoice_status() (which will set custom status to "Paid" if applicable)
                invoice_doc_to_update.validate() 
                
                # 2. Now save the POS Invoice document.
                # The .save() method will persist the changes made by .validate() (new paid_amount, new status)
                # and will also trigger POSInvoice.on_update_after_submit() if it was already submitted,
                # which in turn handles the table status update.
                invoice_doc_to_update.save(ignore_permissions=True) # Use ignore_permissions if needed for system updates
                
                frappe.db.commit()  # Ensure changes to POS Invoice are immediately committed to the DB

                # Optional: If you want a silent confirmation or a very subtle UI feedback
                # frappe.show_alert(f"Invoice {invoice_doc_to_update.name} updated due to payment.", indicator='green')

            except Exception as e:
                # Log the full traceback for server-side diagnosis if anything goes wrong
                frappe.log_error(
                    message=frappe.get_traceback(),
                    title=f"Critical Error: Failed to update POS Invoice '{self.pos_invoice}' from POSPaymentEntry '{self.name}' on_submit. Exception: {str(e)}"
                )
                # Optionally, inform the user that an issue occurred in the background,
                # especially if the commit failed or if invoice_doc_to_update couldn't be saved.
                # frappe.msgprint(
                #     f"An error occurred while finalizing updates for invoice {self.pos_invoice}. Please check server logs or contact support if issues persist.",
                #     title="Invoice Update Issue",
                #     indicator='orange' # Use orange for a warning that isn't stopping the current action but indicates a background issue
                # )
        # else:
            # Optional: Log if a payment entry is submitted without a linked invoice, which might be an issue.
            # frappe.log_info(f"POSPaymentEntry {self.name} submitted without a linked POS Invoice.", "POS Payment Audit")