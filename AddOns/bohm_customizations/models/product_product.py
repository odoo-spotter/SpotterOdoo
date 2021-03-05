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
            if record.is_product_variant:
                if record.categ_id.name.lower() == 'radar':
                    family = ''
                    band = ''
                    range_meters = ''
                    dimensions = ''
                    horizontal_fov = ''
                    vertical_fov = ''
                    temperature = ''
                    interface = ''
                    color = ''
                    designator = ''
                    
                    for attr in record.product_template_attribute_value_ids:
                        if 'family' in attr.attribute_id.name.lower():
                            family = attr.x_code.strip()
                        elif 'band' in attr.attribute_id.name.lower():
                            band = attr.x_code.strip()
                        elif 'range' in attr.attribute_id.name.lower():
                            range_meters = attr.x_code.strip()
                        elif 'dimensions' in attr.attribute_id.name.lower():
                            dimensions = attr.x_code.strip()
                        elif 'horizontal' in attr.attribute_id.name.lower():
                            horizontal_fov = attr.x_code.strip()
                        elif 'vertical' in attr.attribute_id.name.lower():
                            vertical_fov = attr.x_code.strip()
                        elif 'temperature' in attr.attribute_id.name.lower():
                            temperature = attr.x_code.strip()
                        elif 'interface' in attr.attribute_id.name.lower():
                            interface = attr.x_code.strip()
                        elif 'color' in attr.attribute_id.name.lower():
                            color = attr.x_code.strip()
                        elif 'designator' in attr.attribute_id.name.lower():
                            designator = attr.x_code.strip()
                    
                    default_code = '%s%s%s-%s-%s%s%s-%s-%s' % (
                        family, band, range_meters, dimensions, horizontal_fov, vertical_fov, temperature, interface, color)
                    record.update({
                        'default_code': default_code
                    })
                
                elif record.categ_id.name.lower() == 'nio':
                    nio_type = ''
                    connections = ''
                    machine_learning = ''
                    designator = ''
                    
                    for attr in record.product_template_attribute_value_ids:
                        if 'type' in attr.attribute_id.name.lower():
                            nio_type = attr.x_code.strip()
                        elif 'connections' in attr.attribute_id.name.lower():
                            connections = attr.x_code.strip()
                        elif 'machine' in attr.attribute_id.name.lower():
                            machine_learning = attr.x_code.strip()
                        # elif 'designator' in attr.attribute_id.name.lower():
                        #     designator = attr.x_code.strip()
                    
                    default_code = 'NIO-%s-%s-%s' % (nio_type,connections,machine_learning)
                    record.update({
                        'default_code': default_code
                    })
                else:
                    record.default_code = record.name
            else:
                record.default_code = record.name
