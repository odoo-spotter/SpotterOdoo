# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomStockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    x_ticket_id = fields.Many2one(
        'helpdesk.ticket', string='Linked Ticket', ondelete="set null")


    def button_validate(self):
        res = super(CustomStockPicking, self).button_validate()
        
        delivery_type = self.env['stock.picking.type'].search([('name', 'ilike', 'Delivery')], limit=1)
        if not self.carrier_tracking_ref and self.picking_type_id.id == delivery_type.id:
            raise ValidationError(_('Please supply the Tracking Reference in the Additional Info tab for this order.'))

        return res