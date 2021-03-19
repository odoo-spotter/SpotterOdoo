# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import _, api, fields, models

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
