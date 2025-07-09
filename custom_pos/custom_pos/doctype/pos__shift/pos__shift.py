# Copyright (c) 2024, Your Name and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class POSShift(Document):
    def before_save(self):
        """
        Controller hook that runs before the document is saved.
        If the shift status is changed to 'Closed', it calculates the
        expected closing amount based on cash payments received during the shift.
        """
        
        if self.status == "Closed":
            self.calculate_expected_closing_amount()

    def calculate_expected_closing_amount(self):
        """
        Calculates the sum of all 'Cash' payments linked to invoices from this shift
        and adds it to the opening amount.
        """
        
        invoices_in_shift = frappe.get_all(
            "POS Invoice",
            filters={"pos_shift": self.name, "docstatus": 1},
            pluck="name"
        )

        total_cash_payments = 0
        if invoices_in_shift:
            
            cash_payments = frappe.get_all(
                "POS Payment Entry",
                filters={
                    "pos_invoice": ["in", invoices_in_shift],
                    "mode_of_payment": "Cash", 
                    "docstatus": 1,
                },
                fields=["amount"],
            )
            
            
            total_cash_payments = sum([p.amount for p in cash_payments])
            # self.paid_amount = sum(flt(p.get("amount", 0)) for p in payment_entries) # Use .get for safety


        
        self.expected_closing_amount = self.opening_amount + total_cash_payments