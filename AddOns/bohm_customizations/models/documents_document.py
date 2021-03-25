# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

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
        ('approved', 'Approved'),
        ('archived', 'Archived')
    ], 'Status', default='draft', index=True, required=True, copy=False, tracking=True)

    def action_view_document_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Version History'),
            'res_model': 'documents.document',
            'view_mode': 'tree,form',
            'domain': ['|', ('active', '=', True), ('active', '=', False), ('x_original_version', '=', self.x_original_version.id)]
        }

    @api.depends('x_original_version')
    def _compute_related_documents(self):
        for record in self:
            if record.x_original_version:
                related_documents = record.env['documents.document'].with_context(active_test=False).search([
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

    def action_new_version(self):
        self.ensure_one()
        if not self.x_original_version:
            raise ValidationError(
                'Please set the original version to create a new version.')

        else:
            vals = {
                'x_original_version': self.x_original_version.id,
                'folder_id': self.folder_id.id
            }
            new_doc = self.create(vals)

            original_name = self.x_original_version.name.rsplit('.', 1)

            new_doc.name = original_name[0] + \
                '-' "%02d" % (new_doc.x_version,)

            self.message_post(body=_(
                'Version %s <a href=# data-oe-model=documents.document data-oe-id=%d>%s</a> has been created.') % (new_doc.x_version, new_doc.id, new_doc.name))

            self.toggle_active()

            return {
                'name': new_doc.name,
                'view_mode': 'form',
                'res_model': 'documents.document',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': new_doc.id,
            }

    def toggle_active(self):
        for record in self:
            record.state = 'archived'

        return super(CustomDocumentsDocument, self).toggle_active()

    def write(self, vals):
        if vals.get('state') not in ['approved', None]:
            vals['x_all_users'] = False
            vals['x_partner_ids'] = False

        return super(CustomDocumentsDocument, self).write(vals)

    @api.onchange('name')
    def onchange_name(self):
        if self.x_original_version:
            file_load = self.name.rsplit('.', 1)
            if len(file_load) > 1:
                self.name = self._origin.name + '.' + file_load[1]
            else:
                self.name = self._origin.name

    @api.model
    def create(self, vals):
        res = super(CustomDocumentsDocument, self).create(vals)

        if not vals.get('x_original_version'):
            tech_directory = self.env['documents.folder'].search(
                ['|', ('name', 'ilike', 'knowledge'), ('parent_folder_id.name', 'ilike', 'knowledge')])
            directory_ids = []
            for directory in tech_directory:
                directory_ids.append(directory.id)

            if vals.get('folder_id') in directory_ids:
                seq = str(self.env['ir.sequence'].search(
                    [('name', 'ilike', 'kbdsequence')], limit=1).next_by_id())
                if vals.get('url'):
                    res.name = seq
                else:
                    file_type = vals.get('name').rsplit('.', 1)[1]
                    res.name = seq + '.' + str(file_type)

                res.x_original_version = res

        return res
