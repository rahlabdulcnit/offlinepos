# Copyright (c) 2025, Hayrunnisa and contributors
# For license information, please see license.txt
	
# # custom_pos/custom_pos/doctype/pos_invoice_item/pos_invoice_item.py

# import frappe
# from frappe.model.document import Document
# from frappe.utils import flt # flt is used for safe float conversions

# class POSInvoiceItem(Document):
#     # This 'validate' hook is called when a row in the child table is saved,
#     # or before the parent document (POS Invoice) is saved.
#     def validate(self):
#         self.calculate_amount()

#     def calculate_amount(self):
#         """Calculates the amount for the invoice item."""
#         if self.qty and self.rate:
#             self.amount = flt(self.qty) * flt(self.rate)
#         else:
#             self.amount = 0
        
#         # Note: While this calculates the item's amount, the parent POSInvoice
#         # will be responsible for summing these up to get subtotal/grand_total.





# custom_pos/custom_pos/doctype/pos_invoice_item/pos_invoice_item.py

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class POSInvoiceItem(Document):
    def validate(self):
        # If an item is set, and the rate is 0 or not set,
        # try to fetch it from POS Item master.
        # This allows manual override of rate if user types it in.
        # If rate is already set (non-zero), this won't override it.
        if self.item and not flt(self.rate) > 0: # Check if rate is not positive
            item_doc = frappe.get_cached_doc("POS Item", self.item) # Use get_cached_doc for performance
            if item_doc and flt(item_doc.get("standard_selling_rate")) > 0:
                self.rate = flt(item_doc.get("standard_selling_rate"))
            # else: # If rate still not found, it remains 0 or what it was.
            #     pass # Or you could raise an error if rate is mandatory

        self.calculate_amount()

    def calculate_amount(self):
        """Calculates the amount for the invoice item."""
        if self.qty and self.rate is not None: # check rate is not None
            self.amount = flt(self.qty) * flt(self.rate)
        else:
            self.amount = 0