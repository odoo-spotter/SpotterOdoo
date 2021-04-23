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
        delivery_type = self.env['stock.picking.type'].search(
            [('code', '=', 'outgoing')])
        if not self.carrier_tracking_ref and self.picking_type_id in delivery_type:
            raise ValidationError(
                _('Please supply the Tracking Reference in the Additional Info tab for this order.'))
        

        for line in self.move_line_ids:
            if line.lot_id and line.product_id.tracking == 'serial':
                quants = self.env['stock.quant'].search(
                    [('lot_id', '=', line.lot_id.id), ('location_id', '=', 5)])
                for quant in quants:
                    quant.sudo().unlink()
                
        return super(CustomStockPicking, self).button_validate()
