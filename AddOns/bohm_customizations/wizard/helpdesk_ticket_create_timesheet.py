from odoo import api, fields, models, _
from datetime import datetime
from odoo.exceptions import UserError

class HelpdeskTicketCreateTimesheet(models.TransientModel):
    _name = 'helpdesk.ticket.create.timesheet'
    _description = "Create Timesheet from task"

    _sql_constraints = [('time_positive', 'CHECK(time_spent > 0)',
                         'The timesheet\'s time must be positive')]

    @api.model
    def default_get(self, fields):
        result = super(HelpdeskTicketCreateTimesheet, self).default_get(fields)
        active_model = self._context.get('active_model')
        if active_model != 'helpdesk.ticket':
            raise UserError(_("You can only apply this action from a task."))

        active_id = self._context.get('active_id')
        if 'helpdesk_ticket' in fields and active_id:
            helpdesk_ticket = self.env['helpdesk.ticket'].browse(active_id)
            result['helpdesk_ticket'] = active_id
            result['description'] = helpdesk_ticket.name
        return result

    time_spent = fields.Float('Time', precision_digits=2)
    description = fields.Char('Description')
    helpdesk_ticket = fields.Many2one(
        'helpdesk.ticket', "Ticket", help="Ticket for which we are creating a sales order", required=True)

    def save_timesheet(self):
        values = {
            'helpdesk_ticket_id': self.helpdesk_ticket.id,
            'project_id': self.helpdesk_ticket.project_id.id,
            'date': fields.Date.context_today(self),
            'name': self.description,
            'user_id': self.env.uid,
            'unit_amount': self.time_spent,
        }
        self.helpdesk_ticket.write({
            'timesheet_timer_start': False,
            'timesheet_timer_pause': False,
            'timesheet_timer_last_stop': fields.datetime.now(),
        })
        return self.env['account.analytic.line'].create(values)
