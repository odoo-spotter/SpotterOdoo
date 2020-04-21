# -*- coding: utf-8 -*-

from odoo import api, fields, models, exceptions



class JiraProject(models.Model):

    _inherit = 'project.project'

    def create_jira_dict(self, vals):
#         print("\n\ncreate_jira_dict===============",vals,vals['user_id'])
        project_dict = dict()
        if 'name' in vals:
            project_dict['name'] = vals['name']
        if 'key' in vals:
            project_dict['key'] = vals['key']
        if 'project_type_id' in vals:
            project_dict['projectTypeKey'] = self.env['jira.type'].browse(vals['project_type_id']).key
        if 'user_id' in vals:
            project_dict['lead'] = self.env['res.users'].browse(vals['user_id']).jira_accountId
        if 'project_template_id' in vals:
            project_dict['projectTemplateKey'] = self.env['jira.project.template'].browse(vals['project_template_id']).key
        if 'description' in vals:
            if vals['description']:
                project_dict['description'] = vals['description']
            else:
                project_dict['description'] = ''
        if 'url' in vals:
            if vals['url']:
                project_dict['url'] = vals['url']
            else:
                project_dict['url'] = ''
        if 'category_id' in vals:
            if vals['category_id']:
                project_dict['categoryId'] = self.env['jira.category'].browse(vals['category_id']).jira_id
            else:
                project_dict['categoryId'] = ''

        return project_dict

    @api.model
    def create(self, vals):

        response = False
        if 'disable_mail_mail' not in self.env.context and 'jira_project' in vals and vals['jira_project']:
            project_dict = self.create_jira_dict(vals)
#             print("project_dict===============",project_dict)
            response = self.env['res.company'].search([],limit=1).post('project', project_dict)
            vals['jira_id'] = response.json()['id']

        project = super(JiraProject, self).create(vals)
        if response:
            self = self.with_context(dict(disable_mail_mail=True))
            self.process_response(self.env['res.company'].search([],limit=1).get('project/' + project.jira_id).json())
        return project

    def write(self, vals):
        output = super(JiraProject, self).write(vals)
        if 'disable_mail_mail' not in self.env.context and self.jira_id:
            project_dict = self.create_jira_dict(vals)
            if project_dict:
                response = self.env['res.company'].search([],limit=1).put('project/' + self.jira_id, project_dict)
        return output


    @api.onchange('jira_project')
    def onchange_context(self):
        if self.jira_project:
            if self.user_id and not self.user_id.jira_id:
                self.user_id = False
            return {'domain': {'user_id': [('jira_id', '!=', False)]}}
        else:
            return {'domain': {'user_id': []}}

    def receive_all(self):
        response = self.env['res.company'].search([],limit=1).get('project').json()
        for p in response:
            self.process_response(self.env['res.company'].search([],limit=1).get('project/' + p['key']).json())

    def process_response(self, response):
#         print("\n\n============",response['lead'])
        project_dict = dict(
            jira_id=response['id'],
            key=response['key'],
            description=False,
            user_id=self.env['res.users'].get_user_by_dict(response['lead']).id,
            name=response['name'],
            project_type_id=self.env['jira.type'].key_operation(response['projectTypeKey']).id,
            category_id=False,
            url=False,
            type_ids=[(6, 0, [])],
        )

        if 'projectCategory' in response:
            project_dict['category_id'] = self.env['jira.category'].key_operation(response['projectCategory']['id']).id
        if 'url' in response:
            project_dict['url'] = response['url']
        if response['description']:
            project_dict['description'] = response['description']

        issue_type_ids = list()
        for issue_type in response['issueTypes']:
            issue_type_ids.append(self.env['issue.type'].jira_dict(issue_type).id)
        project_dict['issue_type_ids'] = [(6, 0, issue_type_ids)]

        types = self.env['res.company'].search([],limit=1).get('project/' + response['key'] + '/statuses').json()[0]['statuses']
        type_ids = []
        for t in types:
            type_ids.append(self.env['project.task.type'].jira_dict(t).id)
        project_dict['type_ids'] = [(6, 0, type_ids)]
#         print("\n\n===============",project_dict)
        project = self.search([('key', '=', project_dict['key'])])
        if not project:
            project = self.create(project_dict)
        else:
            project.write(project_dict)

        return project

    def key_operation(self, key):
        project = self.search([('key', '=', key)])
        if not project:
            project = self.process_response(
                self.env['res.company'].search([],limit=1).get('project/' + key).json()
            )
        return project

    def get_jira_id(self, id):
        project = self.search([('jira_id', '=', id)])
        if not project:
            project = self.process_response(
                self.env['res.company'].search([],limit=1).get('project/' + id).json()
            )

        return project

    @api.depends('key')
    def name_get(self):
        result = []
        for project in self:
            if project.key:
                result.append((project.id, '[' + project.key + '] ' + project.name))
            else:
                result.append((project.id, project.name))
        return result

    jira_id = fields.Char()
    key = fields.Char()
    description = fields.Text()
    url = fields.Char()
    user_id = fields.Many2one(default=False)
    project_type_id = fields.Many2one('jira.type')
    project_template_id = fields.Many2one('jira.project.template')
    category_id = fields.Many2one('jira.category')
    issue_type_ids = fields.Many2many('issue.type', string='Issue Types')
    jira_project = fields.Boolean(default=True)

