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
        ('updating', 'Needs Updating'),
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

    @api.model
    def create(self, vals):
        tech_directory = self.env['documents.folder'].search(
            [('name', 'ilike', 'tech')], limit=1)

        if vals.get('folder_id') == tech_directory.id:
            file_type = vals.get('name').rsplit('.')[1]
            vals['name'] = str(self.env['ir.sequence'].search(
                [('name', 'ilike', 'tech')]).next_by_id()) + '.' + str(file_type)

        return super(CustomDocumentsDocument, self).create(vals)
