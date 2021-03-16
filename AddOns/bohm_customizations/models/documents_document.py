# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class CustomDocumentsDocument(models.Model):
    _name = 'documents.document'
    _inherit = 'documents.document'

    x_version = fields.Float(
        string='Version',
        digits=(12, 1),
        copy=False,
        store=True,
        compute="_compute_version"
    )

    x_previous_version = fields.Many2one(
        comodel_name='documents.document',
        string="Previous Version"
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved')
    ], 'Status', default='draft', index=True, required=True, copy=False, tracking=True)

    @api.depends('x_previous_version')
    def _compute_version(self):
        if self.x_previous_version:
            self.x_version = self.x_previous_version.x_version + 1
        else:
            self.x_version = 1.0

    def action_draft(self):
        self.state = 'draft'
    
    def action_submit_approval(self):
        self.state = 'pending'
    
    def action_approved(self):
        self.state = 'approved'