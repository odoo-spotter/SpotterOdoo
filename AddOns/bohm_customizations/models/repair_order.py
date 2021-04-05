# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomRepairOrder(models.Model):
    _name = 'repair.order'
    _inherit = 'repair.order'

    state = fields.Selection(
        selection_add=[('waiting', 'Waiting'), ('confirmed',)],
        help="* The \'Draft\' status is used when a user is encoding a new and unconfirmed repair order.\n"
             "* The \'Confirmed\' status is used when a user confirms the repair order.\n"
             "* The \'Waiting\' status is used when a repair is waiting for a customer or another operation.\n"
             "* The \'Ready to Repair\' status is used to start to repairing, user can start repairing only after repair order is confirmed.\n"
             "* The \'To be Invoiced\' status is used to generate the invoice before or after repairing done.\n"
             "* The \'Done\' status is set when repairing is completed.\n"
             "* The \'Cancelled\' status is used when user cancel repair order.")

    x_team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Salesperson"
    )

    def set_to_waiting(self):
        self.state = 'waiting'

    def set_to_draft(self):
        self.state = 'draft'

    def action_validate(self):
        self.ensure_one()
        res = super(CustomRepairOrder, self).action_validate()
        errors = []

        if len(self.fees_lines) == 0 and len(self.operations) == 0:
            errors.append(
                '- You must add Parts or Operations to proceed with this repair.')

        if self.ticket_id and not self.x_studio_is_a_replacement:
            return_receipt = self.env['stock.picking'].search([
                ('x_ticket_id', '=', self.ticket_id.id),
                ('state', 'not in', ['cancel', 'done']),
                ('picking_type_id', '=', self.env['stock.picking.type'].search(
                    [('name', 'ilike', 'RMA'), ('code', '=', 'internal')], limit=1).id)
            ])

            if return_receipt:
                errors.append('- ' + str(return_receipt.name) +
                              ' has not been received. Please receive this return to proceed with this repair.')

        if len(errors):
            msg = 'Please correct the following:\n'
            for error in errors:
                msg += '\n' + str(error)

            raise ValidationError(msg)
        return res

    def action_repair_start(self):
        if self.invoice_method == 'b4repair':
            for invoice in self.invoice_id:
                if invoice.state == 'draft':
                    raise ValidationError(
                        'This repair cannot be started until the attached invoice has posted.')

        return super(CustomRepairOrder, self).action_repair_start()

    def action_repair_invoice_create(self):
        res = super(CustomRepairOrder, self).action_repair_invoice_create()

        for record in self:
            for invoice in record.invoice_id:
                try:
                    if record.ticket_id.x_studio_bdm_2.user_partner_id not in invoice.message_partner_ids:
                        invoice.sudo().message_subscribe(
                            [record.ticket_id.x_studio_bdm_2.user_partner_id.id])
                except:
                    pass
        return res

    def create_return_delivery(self):
        if self.ticket_id:
            picking_type = self.env['stock.picking.type'].search(
                [('name', 'ilike', 'RMA'), ('code', '=', 'outgoing')], limit=1)
            location_dest_id = self.env['stock.location'].search(
                [('name', 'ilike', 'Customers'), ('usage', '=', 'customer')], limit=1)

            picking_vals = {
                'picking_type_id': picking_type.id,
                'partner_id': self.address_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': location_dest_id.id,
                'x_ticket_id': self.ticket_id.id,
                'x_studio_field_oB3Pu': self.id
            }

            picking_id = self.env['stock.picking'].create(picking_vals)
            self.message_post(body=_(
                'The Return Delvery Order <a href=# data-oe-model=stock.picking data-oe-id=%d>%s</a> has been created.') % (picking_id.id, picking_id.name))

            if self.product_id.tracking == 'serial':
                move = self.env['stock.move']

                if self.lot_id:
                    move.picking_create_move(
                        picking_id,  self.product_id, 1, self.location_id, location_dest_id, self.lot_id)
                else:
                    move.picking_create_move(
                        picking_id,  self.product_id, 1, self.location_id, location_dest_id)
