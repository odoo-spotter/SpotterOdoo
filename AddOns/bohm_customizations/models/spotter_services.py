# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SpotterServices(models.Model):
    _name = 'spotter.services'
    _description = 'Spotter Services'
    _order = 'sequence'

    name = fields.Char('Service Name')
    daily_multiplier = fields.Float(string="Daily Multiplier")
    sequence = fields.Integer()
    notes = fields.Char('Notes')

