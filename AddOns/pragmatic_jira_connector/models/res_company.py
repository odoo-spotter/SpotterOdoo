# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions, _
from datetime import datetime, date
from odoo.tools import config
import requests
import os
import logging

class Jira_Config_Settings(models.Model):

    _inherit = 'res.company'
    _description = 'Jira Configuration'
    
    name = fields.Char(default='Jira Settings')
    jira_url = fields.Char('Instance URL')
    jira_login = fields.Char()
    password = fields.Char(string ='Jira Token')


    def get(self, request, path='/rest/api/latest/', check=True):
        response = requests.get(self.jira_url + path + request, auth=(self.jira_login, self.password))
        if check:
            self.check_response(response)
        return response

    def get_file(self, jira_url):
        print('Request For GET', jira_url)
        response = requests.get(jira_url, auth=(self.jira_login, self.password), stream=True)
        self.check_response(response)
        return response

    def post(self, request, rdata=dict(), path='/rest/api/latest/'):
        print('Request For POST', self.jira_url + path + request, rdata)
        response = requests.post(self.jira_url + path + request, auth=(self.jira_login, self.password), json=rdata)
        self.check_response(response)
        return response

    def post_file(self, request, filename, filepath):
        print('Request For POST', self.jira_url + '/rest/api/latest/' + request)
        attachment = open(filepath, "rb")
        response = requests.post(self.jira_url + '/rest/api/latest/' + request, auth=(self.jira_login, self.password),
            files={'file': (filename, attachment, 'application/octet-stream')},
            headers={'content-type': None, 'X-Atlassian-Token': 'nocheck'})
        self.check_response(response)
        return response

    def put(self, request, rdata=dict(), path='/rest/api/latest/'):
        print('Request For PUT', self.jira_url + path + request, rdata)
        response = requests.put(self.jira_url + path + request, auth=(self.jira_login, self.password), json=rdata)
        self.check_response(response)
        return response
    
    def delete(self, request, path='/rest/api/latest/'):
        print('Request For DELETE', self.jira_url + path + request)
        response = requests.delete(self.jira_url + path + request, auth=(self.jira_login, self.password))
        self.check_response(response)
        return response

    def check_response(self, response):
        if response is False:
            return
        if response.status_code not in [200, 201, 204, 404]:
            try:
                resp_dict = response.json()
            except:
                raise exceptions.Warning('Response status code: ' + str(response.status_code))
            error_msg = ''
            if 'errorMessages' in resp_dict and resp_dict['errorMessages']:
                for e in resp_dict['errorMessages']:
                    error_msg += e + '\n'
            if 'errors' in resp_dict and resp_dict['errors']:
                for e in resp_dict['errors']:
                    error_msg += resp_dict['errors'][e] + '\n'
            raise exceptions.Warning(error_msg)

    def getall(self, request, path='/rest/api/latest/', searchobj='issues'):
        companies = self.env['res.company'].search([],limit=1).search([])
        startat = 0
        full_response = list()
        while True:
            response = self.get(request + '&startAt=' + str(startat), path).json()
            if 'errorMessages' in response:
                return full_response
            startat += 50
            if type(response) is list:
                full_response += response
                responselen = len(response)
            else:
                full_response.append(response[searchobj])
                responselen = len(response[searchobj])
            if responselen < 50:
                break
        return full_response
    
    def sendMessage(self, response):
        message = ''
        if 'Message' in response:
            message=response['Message']
        view_id = self.env.ref('pragmatic_jira_connector.response_message_wizard_form').id
        if view_id:
            value = {
                'name': _('Message'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'response.message.wizard',
                'view_id': False,
                'context': {'message': message},
                'views': [(view_id, 'form')],
                'type': 'ir.actions.act_window',
                'target': 'new',
            }
            return value

    def test_connection(self):
        status_code = self.get('myself').status_code
        if status_code == 200:
            return self.sendMessage({'Message':"Connection Check to Jira Successful !!"})
        else:
            return self.sendMessage({'Message':"Connection Check to Jira Unsuccessful !!"})
    
    def update_created_edited_issue(self):
        task_ids = self.env['project.task'].search([('project_id', '!=',None)])
        for task_id in task_ids :
            task_id.record_update()
    
    def record_update(self):
        models = ['res.users', 'jira.category', 'jira.project.template', 'jira.type', 'project.project', 
                  'issue.priority', 'issue.status.category','project.task.type', 'issue.type', 'jira.issue.link.type',
                  'project.task'] 
        if 'update' in self.env.context:
            models = [self.env.context['update']]

        for model in models:
            self.env[model].receive_all()

    def latest_jira_issue_update(self):
        self.env['project.task'].latest_jira_issue_update()

    def update_jira_issues(self):
        models = ['project.task']
        if 'update' in self.env.context:
            models = [self.env.context['update']]

        for model in models:
            self.env[model].receive_all()

    @api.constrains('jira_url')
    def constrains_jira_url(self):
        if not self.jira_url:
            return
        if not self.jira_url.startswith('http://') and not self.jira_url.startswith('https://'):
            raise exceptions.Warning('Url must start with http:// or https://')
        if self.jira_url.endswith('/'):
            self.jira_url = self.jira_url[:-1]

    