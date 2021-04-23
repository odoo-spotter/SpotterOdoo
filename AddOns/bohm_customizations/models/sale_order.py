# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class BohmCustomSaleOrder(models.Model):
    _name = 'sale.order'
    _inherit = 'sale.order'

    def write(self, vals):
        for record in self:
            res = super(BohmCustomSaleOrder, record).write(vals)
            try:
                record.update_leads()
            except:
                pass

            return res

    def update_leads(self):
        if self.opportunity_id:
            total = 0
            sale_orders = self.env['sale.order'].search(
                [('opportunity_id', '=', self.opportunity_id.id), ('state', 'in', ['done', 'sale'])])
            if not len(sale_orders):
                sale_orders = self.env['sale.order'].search(
                    [('opportunity_id', '=', self.opportunity_id.id), ('state', '!=', 'cancel')])

            if self.opportunity_id.stage_id.id == 6 or self.opportunity_id.stage_id.is_won:
                for order in sale_orders:
                    total += order.amount_total
                self.opportunity_id.sudo().write(
                    {'planned_revenue': total})
