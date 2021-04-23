# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class CustomGoalsRepairOrder(models.Model):
    _name = 'repair.order'
    _inherit = 'repair.order'

    x_confirmed_date = fields.Datetime(string="Confirmed Date")

    def write(self, vals):
        res = super(CustomGoalsRepairOrder, self).write(vals)
        for record in self:
            try:
                if vals.get('state') in ['confirmed', '2binvoiced'] and record.x_team_id:
                    record.x_confirmed_date = datetime.datetime.now()
                    record.x_team_id.sudo().refresh_total()
                if vals.get('x_team_id'):
                    record.x_team_id.sudo().refresh_total()
                if vals.get('state') in ['cancel', 'draft'] and record.x_team_id:
                    record.x_confirmed_date = None
                    record.x_team_id.sudo().refresh_total()
            except:
                pass
        return res
