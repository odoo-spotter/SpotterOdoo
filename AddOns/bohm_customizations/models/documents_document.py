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
        compute="_compute_related_documents"
    )

    x_original_version = fields.Many2one(
        comodel_name='documents.document',
        string="Original Version"
    )

    x_related_documents = fields.Many2many(
        'documents.document',
        compute="_compute_related_documents"
    )

    x_updates = fields.Text(
        'Updates',
        help="What was changed?"
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('updating', 'Needs Updating'),
        ('approved', 'Approved')
    ], 'Status', default='draft', index=True, required=True, copy=False, tracking=True)

    @api.depends('x_original_version')
    def _compute_related_documents(self):
        for record in self:
            if record.x_original_version:
                related_documents = record.env['documents.document'].search([
                    '|',
                    ('id', '=', record.x_original_version.id),
                    ('x_original_version', '=', record.x_original_version.id)
                ], order="create_date asc")

                record.x_related_documents = related_documents
                version = 1
                for i, doc in enumerate(related_documents):
                    if doc.id == record._origin.id:
                        version = i + 1

                record.x_version = version
            else:
                record.x_related_documents = None
                record.x_version = 1

    def action_draft(self):
        self.state = 'draft'

    def action_submit_approval(self):
        self.state = 'pending'

    def action_approved(self):
        self.state = 'approved'

    @api.model
    def create(self, vals):
        tech_directory = self.env['documents.folder'].search(
            [('name', 'ilike', 'knowledge')], limit=1)

        if vals.get('folder_id') == tech_directory.id:
            seq = str(self.env['ir.sequence'].search(
                [('name', 'ilike', 'knowledge')], limit=1).next_by_id())
            if vals.get('url'):
                vals['name'] = seq
            else:
                file_type = vals.get('name').rsplit('.')[1]
                vals['name'] = seq + '.' + str(file_type)

        return super(CustomDocumentsDocument, self).create(vals)
