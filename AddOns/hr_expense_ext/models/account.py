# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    employee_id = fields.Many2one('hr.employee', string='Responsible Employee', domain="['&',('active', '=', True),'|', ('company_id', '=', False), ('company_id', '=', company_id)]")

class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'
    
    def action_create_expense(self):          
        for record in self:
            #verify employee is tied to journal
            if record.journal_id.x_studio_employee_id:
                employee_id = record.journal_id.x_studio_employee_id
                #Verify that the employee is still active
                if employee_id.active:
                    amount = record.amount * -1
                    name = str(record.name) + " - " + str(record.journal_id.name) + " - " + str(amount)
                    vals = {
                        'unit_amount': amount,
                        'quantity': 1,
                        'employee_id': employee_id,
                        'date': record.date,
                        'name': name,
                        'payment_mode': 'company_account',
                    }
                    record.env['hr.expense'].create(vals)