# -*- coding: utf-8 -*-

from odoo import models, fields, api


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(selection_add=[
        ('BryntumGantt', "Bryntum Gantt")
    ])


class ActWindowView(models.Model):
    _inherit = 'ir.actions.act_window.view'

    view_mode = fields.Selection(selection_add=[
        ('BryntumGantt', "Bryntum Gantt")
    ])
