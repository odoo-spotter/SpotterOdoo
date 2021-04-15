# -*- coding: utf-8 -*-
from datetime import timedelta, datetime
from odoo import models, fields, api
import pytz
import dateutil.parser


class ProjectProject(models.Model):
    _inherit = 'project.project'

    project_start_date = fields.Datetime(string="Project Start Date",
                                         default=datetime.today())


def check_gantt_date(value):
    if isinstance(value, str):
        return dateutil.parser.parse(value, ignoretz=True)
    else:
        return value


class ProjectTask(models.Model):
    _inherit = 'project.task'

    duration = fields.Integer(string="Duration (days)",
                              compute="_compute_duration", store=True)
    percent_done = fields.Integer(string="Done %", default=0)
    parent_index = fields.Integer(string="Parent Index", default=0)
    assigned_ids = fields.Many2many('res.users', string="Assigned resources")
    effort = fields.Integer(string="Effort (hours)", default=0)
    gantt_calendar = fields.Selection([
        ('general', 'General'),
        ('business', 'Business'),
        ('night', 'Night shift')
    ], string="Gantt Calendar", default='general')
    linked_ids = fields.One2many('project.task.linked',
                                 inverse_name='to_id',
                                 string='Linked')
    scheduling_mode = fields.Selection([
        ('Normal', 'Normal'),
        ('FixedDuration', 'Fixed Duration'),
        ('FixedEffort', 'Fixed Effort'),
        ('FixedUnits', 'Fixed Units')
    ], string='Scheduling Mode')
    constraint_type = fields.Selection([
        ('muststarton', 'Must start on'),
        ('mustfinishon', 'Must finish on'),
        ('startnoearlierthan', 'Start no earlier than'),
        ('startnolaterthan', 'Start no later than'),
        ('finishnoearlierthan', 'Finish no earlier than'),
        ('finishnolaterthan', 'Finish no later than')
    ], string='Constraint Type')
    constraint_date = fields.Datetime(string="Constraint Date")
    effort_driven = fields.Boolean(string="Effort Driven", default=False)
    manually_scheduled = fields.Boolean(string="Manually Scheduled",
                                        default=False)

    def write(self, vals):
        response = super(ProjectTask, self).write(vals)
        one_day = timedelta(days=1)

        if 'planned_date_end' in vals:
            end_date = check_gantt_date(vals['planned_date_end'])
            if not self.planned_date_begin:
                self.planned_date_begin = end_date - one_day
            if self.planned_date_begin >= end_date:
                self.planned_date_end = self.planned_date_begin + one_day

        if 'planned_date_begin' in vals:
            begin_date = check_gantt_date(vals['planned_date_begin'])
            if not self.planned_date_end:
                self.planned_date_end = begin_date + one_day
            if self.planned_date_end <= begin_date:
                self.planned_date_begin = self.planned_date_end - one_day

        return response

    @api.onchange('constraint_type')
    def _onchange_constraint_type(self):
        if not self.constraint_type:
            self.constraint_date = None
        else:
            self.constraint_date = {
                'muststarton': self.planned_date_begin,
                'mustfinishon': self.planned_date_end,
                'startnoearlierthan': self.planned_date_begin,
                'startnolaterthan': self.planned_date_begin,
                'finishnoearlierthan': self.planned_date_end,
                'finishnolaterthan': self.planned_date_end
            }[self.constraint_type]

    @api.depends('planned_date_begin', 'planned_date_end')
    def _compute_duration(self):

        tz = pytz.utc

        if type(self.env.user.partner_id.tz) == str:
            tz = pytz.timezone(self.env.user.partner_id.tz) or pytz.utc

        for rec in self:
            if not rec.planned_date_end or not rec.planned_date_begin:
                continue

            start_date = rec.planned_date_begin.astimezone(tz=tz)
            end_date = rec.planned_date_end.astimezone(tz=tz)

            dif = end_date - start_date
            days = 0
            for i in range(dif.days):
                day_name = (start_date + timedelta(days=i)).strftime('%a')
                if day_name not in ('Sat', 'Sun'):
                    days += 1
            rec.duration = days


class ProjectTaskLinked(models.Model):
    _name = 'project.task.linked'
    _description = 'Project Task Linked'

    from_id = fields.Many2one('project.task', ondelete='cascade', string='From')
    to_id = fields.Many2one('project.task', ondelete='cascade', string='To')


class ResUsers(models.Model):
    _inherit = "res.users"

    project_ids = fields.Many2many('project.task', string="Project")
