# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    @api.onchange('product_id', 'company_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.name:
                self.name = self.product_id.display_name or ''
            ## Removing these lines to prevent the Unit Price from being reset when changing product
            # if not self.attachment_number or (self.attachment_number and not self.unit_amount):
            #     self.unit_amount = self.product_id.price_compute('standard_price')[self.product_id.id]
            self.product_uom_id = self.product_id.uom_id
            self.tax_ids = self.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == self.company_id)  # taxes only from the same company
            account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account and self.is_editable:
                self.account_id = account
                
