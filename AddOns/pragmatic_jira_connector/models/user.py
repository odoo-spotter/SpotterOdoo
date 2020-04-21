# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions
import sys


class JiraUser(models.Model):

    _inherit = 'res.users'

    def action_reset_password(self):
        if 'disable_mail_mail' in self.env.context:
            return
        super(JiraUser, self).action_reset_password()

    def receive_all(self):
        response = self.env['res.company'].search([],limit=1).getall('user/search?username="."&includeInactive=true')
        for r in response:
            self.process_response(r)

    def process_response(self, response):
#         print("\n\n response=================",response)
        if 'errorMessages' in response:
            key = response['errorMessages'][0][len('The user with the key \''):-len('\' does not exist')]
            user_dict = dict(
                jira_accountId=key,
                short_name=key,
                login=key,
                name=key,
                jira_active=False,
            )
        else:
            if 'emailAddress' not in response:
                login = response['accountId']
                email = response['accountId']
            else:
                login = response['emailAddress']
                email = response['emailAddress']

            user_dict = dict(
                jira_accountId=response['accountId'],
                login=login,
                email=email,
                name=response['displayName'],
                jira_active=response['active'],
            )
        user = self.env['res.users'].search([('login', '=', user_dict['login'])])
#         print("\n\n\n ================",user)
        if not user:
            user = self.env['res.users'].create(user_dict)
            self.env['hr.employee'].create(dict(user_id=user.id))
        else:
            user.write(user_dict)
        return user

    def key_operation(self, account_id):
        user = self.search([('jira_accountId', '=', account_id)])
#         print("\n\n user-------------->>>>>>>>>",user)
        if not user:
            user = self.process_response(self.env['res.company'].search([],limit=1).get('user?accountId=' + account_id, check=False).json())
#             print("\n\n=============",user)
        return user

    def jira_short_name(self, name):
        user = self.search([('short_name', '=', name)])
        if not user:
            self.receive_all()
            user = self.search([('short_name', '=', name)])
        return user

    def get_user_by_dict(self, user_dict):
#         print("\n\n get_user_by_dict=============",user_dict,self)
        if 'key' in user_dict:
            return self.key_operation(user_dict['key'])
        else:
            return self.key_operation(user_dict['accountId'])

    jira_accountId = fields.Char()
    short_name = fields.Char()
    name = fields.Char(required=1)
    jira_active = fields.Boolean(default=False)
