# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def get_opp_domain(self, partner):
        domain = []
        if not partner.id:
            return []
        if partner.is_company:
            domain = [
                '|', '|', '|', '|', '|', '|', '|', '|', '|',
                ('x_studio_partner_1.id', '=',  partner.id),
                ('x_studio_partner_1', 'child_of',  partner.id),
                ('x_studio_consultant_1.id', '=',  partner.id),
                ('x_studio_consultant_1', 'child_of',  partner.id),
                ('x_studio_distributor.id', '=',  partner.id),
                ('x_studio_distributor', 'child_of',  partner.id),
                ('x_studio_rep_firm.id', '=',  partner.id),
                ('x_studio_rep_firm', 'child_of',  partner.id),
                ('partner_id.id', '=',  partner.id),
                ('partner_id', 'child_of',  partner.id)
            ]
        elif partner.parent_id:
            domain = [
                '|', '|', '|', '|', '|', '|', '|', '|', '|',
                ('x_studio_partner_1.id', '=',  partner.id),
                ('x_studio_partner_1', '=',  partner.parent_id.id),
                ('x_studio_consultant_1.id', '=',  partner.id),
                ('x_studio_consultant_1', '=',  partner.parent_id.id),
                ('x_studio_distributor.id', '=',  partner.id),
                ('x_studio_distributor', '=',  partner.parent_id.id),
                ('x_studio_rep_firm.id', '=',  partner.id),
                ('x_studio_rep_firm', '=',  partner.parent_id.id),
                ('partner_id.id', '=',  partner.id),
                ('partner_id', '=',  partner.parent_id.id)
            ]
        else:
            domain = [
                '|', '|', '|', '|',
                ('x_studio_partner_1.id', '=',  partner.id),
                ('x_studio_consultant_1.id', '=',  partner.id),
                ('x_studio_distributor.id', '=',  partner.id),
                ('x_studio_rep_firm.id', '=',  partner.id),
                ('partner_id.id', '=',  partner.id)
            ]

        return domain

    def _add_end_user(self, domain, partner):
        if partner.is_company:
            domain.insert(0, '|')
            domain.append(('x_studio_end_user.id', '=', partner.id))
            domain.insert(0, '|')
            domain.append(('x_studio_end_user', 'child_of', partner.parent_id.id))
        elif partner.parent_id:
            domain.insert(0, '|')
            domain.append(('x_studio_end_user.id', '=', partner.id))
            domain.insert(0, '|')
            domain.append(('x_studio_end_user', '=', partner.parent_id.id))
        else:
            domain.insert(0, '|')
            domain.append(('x_studio_end_user.id', '=', partner.id))
        
        return domain
    
    def _compute_opportunity_count(self):
        for partner in self:
            domain = self.get_opp_domain(partner)
            opps = []
            if len(domain):
                domain = self._add_end_user(domain, partner)
                domain.append(('type', '=', 'opportunity'))
                opps = self.env['crm.lead'].search(domain)

            partner.opportunity_count_ids = opps
            partner.opportunity_count = len(opps)

    def action_view_opportunity(self):
        self.ensure_one()
        action = self.env.ref('crm.crm_lead_opportunities').read()[0]
        domain = self.get_opp_domain(self)
        domain = self._add_end_user(domain, self)
        domain.append(('type', '=', 'opportunity'))
        action['domain'] = domain
        return action
