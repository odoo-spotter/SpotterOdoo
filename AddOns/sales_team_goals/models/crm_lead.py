# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class CustomGoalsCrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    def write(self, vals):
        res = super(CustomGoalsCrmLead, self).write(vals)
        for record in self:
            try:
                if record.stage_id.is_won:
                    record.team_id.sudo().refresh_total()
            except:
                pass
        return res
