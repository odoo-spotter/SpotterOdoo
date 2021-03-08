# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    default_code = fields.Char(
        string='Internal Reference',
        compute='_compute_default_code',
        readonly=False,
        track_visibility='onchange',
        store=True,
    )

    def update_sku(self):
        self._compute_default_code()

    @api.depends('product_template_attribute_value_ids')
    def _compute_default_code(self):
        for record in self:
            if len(record.product_template_attribute_value_ids) > 0:
                if record.categ_id.name.lower() == 'radar':
                    interface = ''
                    color = ''
                    designator = ''

                    for attr in record.product_template_attribute_value_ids:
                        if 'interface' in attr.attribute_id.name.lower():
                            interface = '-' + str(attr.x_code.strip())
                        elif 'color' in attr.attribute_id.name.lower():
                            color = '-' + str(attr.x_code.strip())
                        elif 'designator' in attr.attribute_id.name.lower():
                            designator = '-' + str(attr.x_code.strip())

                    default_code = '%s%s%s%s' % (
                        str(record.name.strip()), interface, color, designator)

                    record.update({
                        'default_code': default_code.upper()
                    })

                elif record.categ_id.name.lower() == 'nio':
                    machine_learning = ''
                    designator = ''

                    for attr in record.product_template_attribute_value_ids:
                        if 'machine' in attr.attribute_id.name.lower():
                            machine_learning = '-' + str(attr.x_code.strip())
                        elif 'designator' in attr.attribute_id.name.lower():
                            designator = '-' + str(attr.x_code.strip())

                    default_code = '%s%s%s' % (str(record.name.strip()),
                                               machine_learning, designator)
                    record.update({
                        'default_code': default_code
                    })
