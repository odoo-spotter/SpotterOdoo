# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomProductAttributeValue(models.Model):
    _name = 'product.attribute.value'
    _inherit = 'product.attribute.value'

    x_code = fields.Char(string='Code')

class CustomProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    x_code = fields.Char('Code', related="product_attribute_value_id.x_code")