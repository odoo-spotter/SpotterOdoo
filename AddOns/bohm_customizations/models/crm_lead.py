# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomCrmLead(models.Model):
    _name = 'crm.lead'
    _inherit = 'crm.lead'

    x_can_update = fields.Boolean(
        'Can Update',
        compute="_compute_can_update"
    )

    @api.depends('stage_id')
    def _compute_can_update(self):
        if not self.env.user.has_group('base.user_admin') and self.stage_id.is_won:
            self.x_can_update = False
        else:
            self.x_can_update = True

    def write(self, vals):
        if self.stage_id.id == 6 and not self.env.user.has_group('base.user_admin') and vals.get('stage_id'):
            raise ValidationError(
                _('You do not have permission to move Won opportunites, please contact an Admin!')
            )

        if vals.get('stage_id') == 6:
            if len(self.order_ids) < 1 and not self.message_main_attachment_id:
                raise ValidationError(
                    _('An Opportunity cannot be "won" or in PO received without a quotation!'))
            else:
                try:
                    total = 0
                    sale_orders = self.env['sale.order'].search(
                        [('opportunity_id', '=', self.id), ('state', 'in', ['done', 'sale'])])
                    if not len(sale_orders):
                        sale_orders = self.env['sale.order'].search(
                            [('opportunity_id', '=', self.id), ('state', '!=', 'cancel')])
                    for order in sale_orders:
                        total += order.amount_total
                    self.planned_revenue = total
                except:
                    pass

        super(CustomCrmLead, self).write(vals)

        if vals.get('partner_id'):
            try:
                self.action_assign_partner()
            except:
                pass
        return
