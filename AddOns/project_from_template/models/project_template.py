# -*- coding: utf-8 -*-

from odoo import _, fields, models, api
from odoo.exceptions import UserError,ValidationError


class Template(models.Model):
    _name = "project.template"
    _description = "Project template"

    allow_timesheets = fields.Boolean("Timesheets", compute='_compute_allow_timesheets')
    
    def enable_template(self):
        if self.state == 'disabled':
            self.state = 'enabled'

    def disable_template(self):
        if self.state == 'enabled':
            self.state = 'disabled'

    def _compute_allow_timesheets(self):
        for record in self:
            if self.env['ir.module.module'].sudo().search([('name', '=', 'hr_timesheet')]).state == 'installed':
                record.allow_timesheets = True
            else:
                record.allow_timesheets = False
    
    active = fields.Boolean(default=True,
        help="If the active field is set to False, it will allow you to hide the project without removing it.")
    sequence = fields.Integer(default=10, help="Gives the sequence order when displaying a list of Projects.")
    name = fields.Char(string='Name', required=True)
    label_tasks = fields.Char(string='Use Tasks as', default='Tasks',
        required=True, help="Label used for the tasks of the project.")
    description = fields.Text(string="Description")
    template_task_ids = fields.One2many('project.template.task', 'template_id',copy=True, string="Template Task Activities")    
    user_id = fields.Many2one('res.users', string='Project Manager', default=lambda self: self.env.user)
    project_task_type_ids = fields.Many2many(comodel_name='project.task.type', string='Stages in Project')

    state = fields.Selection(string='State',default='disabled', selection=[('disabled', 'Disabled'), ('enabled', 'Enabled'),])

    color = fields.Selection(string='Color', selection=[
        ('0', 'No Color'), 
        ('1', 'Red'),
        ('2', 'Orange'),
        ('3', 'Yellow'),
        ('4', 'Light Blue'),
        ('5', 'Dark Purple'),
        ('6', 'Salmon Pink'),
        ('7', 'Medium Blue'),
        ('8', 'Dark Blue'),
        ('9', 'Fushia'),
        ('10', 'Green'),
        ('11', 'Purple'),
        ], default='0',required=True)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    privacy_visibility = fields.Selection([
            ('followers', 'Invited employees'),
            ('employees', 'All employees'),
            ('portal', 'Portal users and all employees'),
        ],
        string='Visibility', required=True,
        default='portal',
        help="Defines the visibility of the tasks of the project:\n"
                "- Invited employees: employees may only see the followed project and tasks.\n"
                "- All employees: employees may see all project and tasks.\n"
                "- Portal users and all employees: employees may see everything."
                "   Portal users may see project and tasks followed by.\n"
                "   them or by someone of their company.")
    
    resource_calendar_id = fields.Many2one(
        'resource.calendar', string='Working Time',
        default=lambda self: self.env.company.resource_calendar_id.id,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Timetable working hours to adjust the gantt diagram report")
        

class TemplateTask(models.Model):
    
    _name = "project.template.task"
    _description = "Task template"
    _order = "priority desc, sequence, id desc"    
    

    name = fields.Char(string='Title', tracking=True, required=True, index=True)
    description = fields.Html(string='Description')
    
    color = fields.Selection(string='Color', selection=[
        ('0', 'No Color'), 
        ('1', 'Red'),
        ('2', 'Orange'),
        ('3', 'Yellow'),
        ('4', 'Light Blue'),
        ('5', 'Dark Purple'),
        ('6', 'Salmon Pink'),
        ('7', 'Medium Blue'),
        ('8', 'Dark Blue'),
        ('9', 'Fushia'),
        ('10', 'Green'),
        ('11', 'Purple'),
        ], default='0',required=True)
    
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
    ], default='0', index=True, string="Priority")

    to_deadline_count = fields.Integer(
        'Deadline', default=0,
        help='Number of days/week/month to deadline date.')
    
    @api.constrains('to_deadline_count')
    def _check_to_deadline_count(self):
        for record in self:
            if record.to_deadline_count < 0:
                raise ValidationError("Cout to deadline must be greater than zero")

    to_deadline_unit = fields.Selection([
        ('days', 'days'),
        ('weeks', 'weeks'),
        ('months', 'months')], string="Period units", help="Unit of period", required=True, default='days')
    to_deadline_from = fields.Selection([        
        ('start_project_date', 'after start project date'),
        ('previous_task_deadline_date','after previous task deadline')], 
        string="Period Type",required=True, help="Type of period", default='previous_task_deadline_date')

    compute_deadline = fields.Boolean(string='Compute Deadline')    
    
    deadline_formatted = fields.Char(string='Deadline', compute='_compute_deadline_formatted')


    @api.depends('compute_deadline','to_deadline_count','to_deadline_unit','to_deadline_from')
    def _compute_deadline_formatted(self):
        for record in self:
            if record.compute_deadline == True:
                if record.to_deadline_count and record.to_deadline_unit and record.to_deadline_from:
                    record.deadline_formatted = ("%s %s %s")%(str(record.to_deadline_count), 
                    dict(record._fields['to_deadline_unit']._description_selection(record.env)).get(record.to_deadline_unit), 
                    dict(record._fields['to_deadline_from']._description_selection(record.env)).get(record.to_deadline_from))
            else:
                record.deadline_formatted = ''

    allow_timesheets = fields.Boolean("Timesheets", compute='_compute_allow_timesheets')
    
    def _compute_allow_timesheets(self):
        for record in self:
            if self.env['ir.module.module'].sudo().search([('name', '=', 'hr_timesheet')]).state == 'installed':
                record.allow_timesheets = True
            else:
                record.allow_timesheets = False

    template_id = fields.Many2one(comodel_name='project.template', string='Project template')
    sequence = fields.Integer(string='Sequence', index=True, default=10,
        help="Gives the sequence order when displaying a list of tasks.")
    stage_id = fields.Many2one('project.task.type', string='Stage', ondelete='restrict', index=True,
         copy=True)
    
    planned_hours = fields.Float("Planned Hours", help='It is the time planned to achieve the task. If this document has sub-tasks, it means the time needed to achieve this tasks and its childs.',tracking=True)
    
        
    tag_ids = fields.Many2many('project.tags', string='Tags')

    user_id = fields.Many2one('res.users',
        string='Assigned to',
        default=lambda self: self.env.uid,
        )