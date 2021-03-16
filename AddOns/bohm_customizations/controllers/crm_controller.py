from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomWebsiteAccount(CustomerPortal):

    def get_domain_my_lead(self, user):
        if user.partner_id.x_studio_limit_portal_access:
            domain = [('id', '=', False)]
        else:
            domain = user.partner_id.get_opp_domain(user.partner_id)
        domain.append(('type', '=', 'lead'))
        return domain

    def get_domain_my_opp(self, user):
        if user.partner_id.x_studio_limit_portal_access:
            domain = [('id', '=', False)]
        else:
            domain = user.partner_id.get_opp_domain(user.partner_id)
        domain.append(('type', '=', 'opportunity'))
        return domain
