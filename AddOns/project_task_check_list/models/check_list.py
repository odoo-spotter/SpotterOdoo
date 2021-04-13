# -*- coding: utf-8 -*-

from odoo import models, fields


class CheckList(models.Model):
    _name = 'check.list'
    name = fields.Char('Name')
    name_work = fields.Text('Name Work', track_visibility='onchange')
    description = fields.Text('Description')
    status = fields.Selection(string="Status",
                              selection=[('done', 'Done'), ('progress', 'In Progress'), ('cancel', 'Cancel')],
                              readonly=True, track_visibility='onchange')

    def do_accept(self):
        self.write({
            'status': 'done',
        })
        # return {'type': 'ir.actions.client', 'tag': 'reload'}

    def do_cancel(self):
        self.write({
            'status': 'cancel',
        })
        # return {'type': 'ir.actions.client', 'tag': 'reload'}

    def do_progress(self):
        self.write({
            'status': 'progress',
        })
        # return {'type': 'ir.actions.client', 'tag': 'reload'}

    def do_set_to(self):
        self.write({
            'status': ''
        })
