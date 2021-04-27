# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

from odoo import fields, models ,api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    reminder_days = fields.Integer('Reminder Days For Rental Expiration Mail', related='company_id.reminder_days', readonly=False )
    
    @api.onchange('reminder_days')
    def _onchange_reminder_days(self):
        if self.reminder_days:
            company = self.env['res.company']
            company_obj = company.browse(self.company_id.id)
            company_obj.write({'reminder_days':self.reminder_days})
    
    
    
class ResCompany(models.Model):
    _inherit = "res.company"
    
    reminder_days = fields.Integer('Reminder Days For Rental Expiration Mail')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
