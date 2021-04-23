from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import content_disposition, Controller, request, route


class CustomWebsiteAccount(CustomerPortal):

    def get_domain_my_lead(self, user):
        domain = user.partner_id.get_opp_domain(user.partner_id)
        domain.append(('type', '=', 'lead'))
        return domain

    def get_domain_my_opp(self, user):
        domain = user.partner_id.get_opp_domain(user.partner_id)
        domain.append(('type', '=', 'opportunity'))
        return domain

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        values = self._prepare_home_portal_values()
        if request.env.user.partner_id.x_studio_limit_portal_access:
            values['lead_count'] = 0
            values['opp_count'] = 0
            values['quotation_count'] = 0
            values['order_count'] = 0
            values['purchase_count'] = 0
            values['invoice_count'] = 0
            values['subscription_count'] = 0
            
        return request.render("portal.portal_my_home", values)