# -*- coding: utf-8 -*-

from odoo import _,api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from odoo.tools.safe_eval import safe_eval

class CreateProjectFromTemplate(models.TransientModel):
    _name = "project.createfrom.template"
    _description = "Create project from a template"
    
    
    template_id = fields.Many2one(comodel_name='project.template', required=True,  string='Template', domain="[('state','=','enabled')]")

    allow_timesheets = fields.Boolean("Timesheets", default=False)

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

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
        ])
    
    name = fields.Char(string='Name', required=True)
    date_start = fields.Date(string='Start Date')

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.template_task_ids:            
            last_deadline = None
            for task in self.template_task_ids:                
                if task.compute_deadline == True:
                    if task.to_deadline_from == 'start_project_date':
                        project_start_date = fields.Datetime.from_string(self.date_start)
                        if task.to_deadline_unit == 'days':
                            interval = timedelta(days=(task.to_deadline_count))                    
                            task.date_deadline = fields.Datetime.to_string(project_start_date + interval)
                            last_deadline = task.date_deadline
                        elif task.to_deadline_unit == 'weeks':
                            interval = timedelta(weeks=(task.to_deadline_count))                    
                            task.date_deadline = fields.Datetime.to_string(project_start_date + interval)
                            last_deadline = task.date_deadline
                        elif task.to_deadline_unit == 'months':
                            interval = timedelta(days=((task.to_deadline_count)*30))                    
                            task.date_deadline = fields.Datetime.to_string(project_start_date + interval)
                            last_deadline = task.date_deadline
                
                    if  task.to_deadline_from == 'previous_task_deadline_date':
                        if last_deadline == None:
                            project_start_date = fields.Datetime.from_string(self.date_start)
                        else:
                            project_start_date = last_deadline
                        if task.to_deadline_unit == 'days':
                            interval = timedelta(days=(task.to_deadline_count))                    
                            task.date_deadline = fields.Datetime.to_string(project_start_date + interval)
                            last_deadline = task.date_deadline
                        elif task.to_deadline_unit == 'weeks':
                            interval = timedelta(weeks=(task.to_deadline_count))                    
                            task.date_deadline = fields.Datetime.to_string(project_start_date + interval)
                            last_deadline = task.date_deadline
                        elif task.to_deadline_unit == 'months':
                            interval = timedelta(days=((task.to_deadline_count)*30))                    
                            task.date_deadline = fields.Datetime.to_string(project_start_date + interval)
                            last_deadline = task.date_deadline
                        
                    
                    

    partner_id = fields.Many2one('res.partner',
        string='Customer',        
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    
        
    @api.onchange('template_id')
    def onchange_template_id(self):
        if self.template_id:

            if self.template_task_ids:
                    self.template_task_ids = [(5)]

            self.name = '[' + self.template_id.name + '] '
            self.allow_timesheets = self.template_id.allow_timesheets            
            self.label_tasks = self.template_id.label_tasks
            self.user_id = self.template_id.user_id.id
            self.privacy_visibility = self.template_id.privacy_visibility
            self.resource_calendar_id = self.template_id.resource_calendar_id.id
            self.color = self.template_id.color
            
            if self.template_task_ids:
                self.template_task_ids = [(5, _, _)]
                
            
            #We compute the records for stages tree            
            if self.template_id.project_task_type_ids:
                stages = []
                for stage in self.template_id.project_task_type_ids:
                    stages.append(stage.id)            
                self.project_task_type_ids = [(6,0,stages)]
            else:
                if self.project_task_type_ids:
                    self.project_task_type_ids = [(5, _, _)]
            
            if self.template_id.template_task_ids:
                tasks = []
                for task in self.template_id.template_task_ids:                    
                    #Before create the task, we computed tag_ids
                    tags =[]
                    for tag in task.tag_ids:
                        tags.append(tag.id)                    
                    
                    data_task = {
                        'name' : task.name,
                        'compute_deadline': task.compute_deadline,
                        'to_deadline_count': task.to_deadline_count,
                        'to_deadline_unit': task.to_deadline_unit,
                        'to_deadline_from': task.to_deadline_from,                         
                        'color' : task.color,                        
                        'user_id': task.user_id.id,
                        'stage_id': task.stage_id.id,
                        'description': task.description,
                        'priority': task.priority,
                        'sequence': task.sequence,
                        'tag_ids': [(6,0,tags)]
                        }
                    
                    if task.planned_hours > 0 and task.allow_timesheets:
                        data_task['planned_hours'] = task.planned_hours

                    task_item = (0,0,data_task)
                    tasks.append(task_item)
            
                if self.template_task_ids:
                    self.template_task_ids = [(5, _, _)]
                self.template_task_ids = tasks

            
            else:
                
                self.template_task_ids = [(5, _, _)]

                            

            
                
    label_tasks = fields.Char(string='Use Tasks as', default='Tasks', help="Label used for the tasks of the project.")    
    
    template_task_ids = fields.One2many('project.createfrom.template.task', 'template_id', copy=True, string="Template Task Activities")
    
    user_id = fields.Many2one('res.users', string='Project Manager', default=lambda self: self.env.user)

    project_task_type_ids = fields.Many2many(comodel_name='project.task.type', string='Stages in Project')

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
      


    def create_new_project_from_template(self):
        if self.template_id:

            project_data = {
                'name' : self.name,
                'label_tasks': self.label_tasks,                
                'color': int(self.color),
                'user_id': self.user_id.id,
                'partner_id': self.partner_id.id,
                'privacy_visibility': self.privacy_visibility,
                'resource_calendar_id': self.resource_calendar_id.id,                
            }

            #Firs, we create the project and then task and subtasks
                        
            
            tasks = []
            if self.template_task_ids:
                for task in self.template_task_ids:
                    tags =[]
                    for tag in task.tag_ids:
                        tags.append(tag.id)
                    
                    data_task = {                        
                        'name' : task.name,                        
                        'user_id': task.user_id.id,                        
                        'stage_id': task.stage_id.id,
                        'date_deadline': task.date_deadline,
                        'planned_hours': task.planned_hours,
                        'description': task.description,
                        'priority': task.priority,
                        'sequence': task.sequence,
                        'color' : task.color,
                        'tag_ids': [(6,0,tags)]
                        }                    
                    
                    task_item = (0,0,data_task)
                    tasks.append(task_item)            
           
                project_data['task_ids'] = tasks

            res_project = self.env['project.project'].create(project_data)

            for stage in self.project_task_type_ids:
                stage.project_ids = [(4,res_project.id)]

            action = self.with_context(active_id=res_project.id).env.ref('project.act_project_project_2_project_task_all').read()[0]
            
            if action.get('context'):
                eval_context = self.env['ir.actions.actions']._get_eval_context()
                eval_context.update({'active_id': res_project.id})
                action['context'] = safe_eval(action['context'], eval_context)
            
            action.setdefault('context', {})
            return action
        
        else:
            raise UserError(_("You need to select a template"))

class CreateTaskFromTemplate(models.TransientModel):
    
    _name = "project.createfrom.template.task"
    _description = "Task template"
    _order = "priority desc, sequence, id desc"    
    

    name = fields.Char(string='Title', index=True)
    description = fields.Html(string='Description')

    allow_timesheets = fields.Boolean("Timesheets", default=False)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Important'),
    ], default='0', index=True, string="Priority")

    template_id = fields.Many2one(comodel_name='project.createfrom.template', string='Project template')
    sequence = fields.Integer(string='Sequence', index=True, default=10,
        help="Gives the sequence order when displaying a list of tasks.")
    stage_id = fields.Many2one('project.task.type', string='Stage', ondelete='restrict', index=True,
         copy=True)
    
    planned_hours = fields.Float("Planned Hours", help='It is the time planned to achieve the task. If this document has sub-tasks, it means the time needed to achieve this tasks and its childs.',tracking=True)
    
        
    tag_ids = fields.Many2many('project.tags', string='Tags')    

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
        ])

    date_deadline = fields.Date(string='Deadline', index=True, copy=False)
    
    user_id = fields.Many2one('res.users',
        string='Assigned to',
        default=lambda self: self.env.uid,
        )
    
    to_deadline_count = fields.Integer(
        'Deadline', default=0,
        help='Number of days/week/month to deadline date.')    
    
    to_deadline_unit = fields.Selection([
        ('days', 'days'),
        ('weeks', 'weeks'),
        ('months', 'months')], string="Period units", help="Unit of period",  default='days')
    to_deadline_from = fields.Selection([        
        ('start_project_date', 'after start project date'),
        ('previous_task_deadline_date','after previous task deadline')], string="Period Type", help="Type of period", default='previous_task_deadline_date')

    compute_deadline = fields.Boolean(string='Compute Deadline')

