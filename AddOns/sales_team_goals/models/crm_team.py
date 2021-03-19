# -*- coding: utf-8 -*-
import logging
import datetime

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class CustomCrmTeam(models.Model):
    _name = 'crm.team'
    _inherit = 'crm.team'

    x_goals_lines = fields.One2many(
        comodel_name="crm.sales_goals_line",
        inverse_name="x_team_id",
        string='Sales Goals'
    )

    def refresh_total(self):
        for record in self.x_goals_lines:
            start_month = datetime.date(
                int(record.x_goal_year), int(record.x_goal_month), 1)
            end_month = self.last_day_of_month(datetime.date(
                int(record.x_goal_year), int(record.x_goal_month), 1))

            leads = record.env['crm.lead'].search([('team_id', '=', record.x_team_id.id), ('stage_id.is_won', '=', True), (
                'date_closed', '>=', start_month), ('date_closed', '<=', end_month)])

            repairs = record.env['repair.order'].search([('x_team_id', '=', record.x_team_id.id), (
                'x_confirmed_date', '>=', start_month), ('x_confirmed_date', '<=', end_month)])

            total = 0

            for lead in leads:
                total += lead.planned_revenue
            for repair in repairs:
                total += repair.amount_total

            record.x_total_reached = total
            record.x_total_remaining = record.x_goal_amount - record.x_total_reached

    def last_day_of_month(self, any_day):
        next_month = any_day.replace(day=28) + datetime.timedelta(days=4)
        return next_month - datetime.timedelta(days=next_month.day)

    def update_all(self):
        sales_teams = self.search([])
        for team in sales_teams:
            team.refresh_total()


class CrmTeamSalesGoalMonthLines(models.Model):
    _name = 'crm.sales_goals_line'

    x_team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Sales Team"
    )

    x_goal_month = fields.Selection(selection=[
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')], string="Month", required=True)

    x_goal_year = fields.Selection(
        selection='_get_selection', string='Year', required=True,
        default=lambda x: str(datetime.datetime.now().year))

    x_goal_amount = fields.Float(
        'Goal Amount', required=True)

    x_total_reached = fields.Float(
        'Total Sales'
    )

    x_total_remaining = fields.Float(
        'Total Remaining'
    )

    def _get_selection(self):
        current_year = datetime.datetime.now().year
        return [(str(i), i) for i in range(current_year - 10, current_year + 10)]
