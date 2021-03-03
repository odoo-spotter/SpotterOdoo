# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomHelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _inherit = 'helpdesk.ticket'

    x_repair_pickings_count = fields.Integer(
        'RMA Receipt Count', compute="_compute_rma_count")
    picking_ids = fields.Many2many('stock.picking', string="Return Orders")

    @api.depends('picking_ids')
    def _compute_rma_count(self):
        for ticket in self:
            ticket.x_repair_pickings_count = len(
                self.env['stock.picking'].search([('x_ticket_id', '=', ticket.id)]))

    def action_view_rma_receipts(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('RMA Receipts'),
            'res_model': 'stock.picking',
            'view_mode': 'tree,form',
            'domain': [('x_ticket_id', '=', self.id)],
            'context': dict(self._context, create=False, default_company_id=self.company_id.id)
        }

    def action_repair_receive(self):
        action = self.env.ref(
            'helpdesk_repair.action_repair_order_form').read()[0]

        context = {
            'default_partner_id': self.partner_id.id,
            'default_ticket_id': self.id
        }

        if self.product_id:
            context['default_product_id'] = self.product_id.id
        if self.lot_id:
            context['default_lot_id'] = self.lot_id.id

        action.update({
            'context': context
        })

        self.create_rma_receipt()

        return action

    def create_rma_receipt(self):
        picking_type = self.env['stock.picking.type'].search(
            [('name', 'ilike', 'RMA')], limit=1
        )
        location_id = self.env['stock.location'].search(
            [('name', 'ilike', 'Customers'), ('usage', '=', 'customer')], limit=1
        )
        location_dest_id = self.env['stock.location'].search(
            [('name', 'ilike', 'Repair')], limit=1
        )

        picking_vals = {
            'picking_type_id': picking_type.id,
            'partner_id': self.partner_id.id,
            'location_id': location_id.id,
            'location_dest_id': location_dest_id.id,
            'x_ticket_id': self.id
        }

        picking_id = self.env['stock.picking'].create(picking_vals)

        self.message_post(body=_(
            'The RMA Receipt <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created and is waiting for the customer.') % (picking_id.id, picking_id.name))

        if self.product_id and self.product_id.tracking == 'serial':
            move = self.env['stock.move']

            if self.lot_id:
                move.picking_create_move(
                    picking_id,  self.product_id, 1, location_id, location_dest_id, self.lot_id)
            else:
                move.picking_create_move(
                    picking_id,  self.product_id, 1, self.location_id, location_dest_id)
