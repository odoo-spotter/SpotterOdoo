# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CustomResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        try:
            parent_id = vals.get('parent_id')
            if parent_id:
                parent = self.search([('id', '=', parent_id)])
                if not vals.get('x_studio_customer_type'):
                    vals['x_studio_customer_type'] = parent.x_studio_customer_type
                if not vals.get('x_studio_vertical'):
                    vals['x_studio_vertical'] = parent.x_studio_vertical
                if not vals.get('team_id'):
                    vals['team_id'] = parent.team_id.id
        except:
            pass

        return super(CustomResPartner, self).create(vals)

    @api.onchange('x_studio_customer_type')
    def update_child_type(self):
        try:
            for record in self:
                origin = record._origin
                for child in origin.child_ids:
                    child.x_studio_customer_type = record.x_studio_customer_type
        except:
            pass
    
    def _invoice_total(self):
        for record in self:
            record.total_invoiced = 0

    @api.onchange('x_studio_vertical')
    def update_child_vertical(self):
        try:
            for record in self:
                origin = record._origin
                for child in origin.child_ids:
                    child.x_studio_vertical = record.x_studio_vertical
        except:
            pass
    
    @api.onchange('team_id')
    def update_child_team(self):
        try:
            for record in self:
                origin = record._origin
                for child in origin.child_ids:
                    child.team_id = record.team_id
        except:
            pass
    
    def get_opp_domain(self, partner):
        domain = []
        if not partner.id:
            return None
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
            domain.append(('x_studio_end_user', 'child_of', partner.id))
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
            if domain:
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
