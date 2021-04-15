# -*- coding: utf-8 -*-
import re
import dateutil.parser
from json import dumps, loads
import base64

import pytz

from odoo import http
from odoo.http import Response, request


class BryntumGantt(http.Controller):
    task_id_template = 'project-task_%d'

    @staticmethod
    def get_gantt_date(date_field, tz=None):
        if not date_field:
            return ''
        if tz and hasattr(date_field, 'astimezone'):
            return date_field.astimezone(tz).strftime('%Y-%m-%d')
        return date_field.strftime('%Y-%m-%d')

    @staticmethod
    def from_gantt_date(value):
        return dateutil.parser.parse(value, ignoretz=True)

    @staticmethod
    def field_related(data, cfields):
        response = {}
        for o_key, g_key, func in cfields:
            value = data.get(g_key, '0_empty_value_0')
            if value == '0_empty_value_0':
                continue
            if func and not value is None:
                response.update({o_key: func(value)})
            else:
                response.update({o_key: value})
        return response

    @staticmethod
    def to_id(gantt_id):
        groups = re.match(r'project-task_(\d+)', gantt_id)
        if groups:
            return int(groups.group(1))
        return 0

    @staticmethod
    def is_gantt_new_id(new_id):
        return bool(re.match(r'_generated.+\d+', new_id))

    def get_tz(self):
        return pytz.timezone(request.env.user.partner_id.tz) or pytz.utc

    @property
    def default_fields(self):
        return [
            ('name', 'name', None),
            ('planned_date_begin', 'startDate', self.from_gantt_date),
            ('planned_date_end', 'endDate', self.from_gantt_date),
            ('parent_id', 'parentId', self.to_id),
            ('parent_index', 'parentIndex', None),
            ('percent_done', 'percentDone', None),
            ('assigned_ids', 'assignedList', None),
            ('description', 'note', None),
            ('effort', 'effort', None),
            ('gantt_calendar', 'calendar', None),
            ('date_deadline', 'date_deadline', self.from_gantt_date),
            ('scheduling_mode', 'schedulingMode', None),
            ('constraint_type', 'constraintType', None),
            ('constraint_date', 'constraintDate', self.from_gantt_date),
            ('effort_driven', 'effortDriven', None),
            ('manually_scheduled', 'manuallyScheduled', None),
        ]

    @property
    def gantt_calendar(self):
        return [
            {
                "id": "general",
                "name": "General",
                "intervals": [
                    {
                        "recurrentStartDate": "on Sat at 0:00",
                        "recurrentEndDate": "on Mon at 0:00",
                        "isWorking": False
                    }
                ],
                "expanded": True,
                "children": [
                    {
                        "id": "business",
                        "name": "Business",
                        "hoursPerDay": 8,
                        "daysPerWeek": 5,
                        "daysPerMonth": 20,
                        "intervals": [
                            {
                                "recurrentStartDate": "every weekday at 12:00",
                                "recurrentEndDate": "every weekday at 13:00",
                                "isWorking": False
                            },
                            {
                                "recurrentStartDate": "every weekday at 17:00",
                                "recurrentEndDate": "every weekday at 08:00",
                                "isWorking": False
                            }
                        ]
                    },
                    {
                        "id": "night",
                        "name": "Night shift",
                        "hoursPerDay": 8,
                        "daysPerWeek": 5,
                        "daysPerMonth": 20,
                        "intervals": [
                            {
                                "recurrentStartDate": "every weekday at 6:00",
                                "recurrentEndDate": "every weekday at 22:00",
                                "isWorking": False
                            }
                        ]
                    }
                ]
            }
        ]

    @http.route('/bryntum_gantt_enterprise/load', method='POST', type='http', auth='user')
    def bryntum_gantt_load(self, project_id=None, **kw):
        headers = {'content-type': 'application/json'}

        # user = request.env.user
        project_env = request.env['project.project']
        # task_env = request.env['project.task']
        user_env = request.env['res.users']

        if project_id:
            project_id = int(project_id)
        else:
            project_id = 0

        project = project_env.search([('id', '=', project_id)])
        task_ids = project.task_ids

        user_ids = user_env.search([])

        tz = self.get_tz()

        tasks = [
            {
                "id": self.task_id_template % task.id,
                "name": task.name,
                "parentId": self.task_id_template % task.parent_id,
                "parentIndex": task.parent_index,
                "percentDone": task.percent_done,
                "startDate": self.get_gantt_date(task.planned_date_begin, tz),
                "endDate": self.get_gantt_date(task.planned_date_end, tz),
                "expanded": True,
                "date_deadline": self.get_gantt_date(task.date_deadline, tz),
                "note": task.description,
                "effort": task.effort,
                "duration": task.duration,
                "calendar": task.gantt_calendar,
                "schedulingMode": task.scheduling_mode,
                "constraintType": task.constraint_type or None,
                "constraintDate": self.get_gantt_date(task.constraint_date, tz),
                "effortDriven": task.effort_driven,
                "manuallyScheduled": task.manually_scheduled
            }
            for task in task_ids
        ]

        users = [
            {
                "id": user.id,
                "name": user.name,
                "city": user.partner_id.city
#                 "avatar": base64.b64encode(user.partner_id.image_1920).decode('ascii')
            }
            for user in user_ids
        ]

        assignments = [
            {
                "id": '%d-%d' % (task.id, user.id),
                "event": self.task_id_template % task.id,
                "resource": user.id,
            }
            for task in task_ids
            for user in task.assigned_ids or []
        ]

        dependencies = [
            {
                'id': link.id,
                'fromTask': self.task_id_template % link.from_id,
                'toTask': self.task_id_template % link.to_id
            }
            for task in task_ids for link in task.linked_ids
        ]

        params = {
            "success": True,
            "project": {
                'id': 'project_%d' % project,
                "calendar": "general",
                "startDate": self.get_gantt_date(project.project_start_date,
                                                     tz)
            },
            "calendars": {
                "rows": self.gantt_calendar
            },
            "tasks": {
                "rows": [{
                    'id': 'project-project_%d' % project,
                    "startDate": self.get_gantt_date(project.project_start_date,
                                                     tz),
                    'name': project.name,
                    'expanded': True,
                    'children': tasks
                }]
            },
            "dependencies": {
                "rows": dependencies,
            },
            "resources": {
                "rows": users
            },
            "assignments": {
                "rows": assignments
            },
            "timeRanges": {
                "rows": []
            }
        }
        return Response(response=dumps(params), headers=headers)

    @staticmethod
    def gantt_id(_id):
        response = re.match(r'(project-task)_(\d+)', _id) \
                   or re.match(r'(project-project)_(\d+)', _id) \
                   or re.match(r'(project)_(\d+)', _id)
        if response:
            return response.group(1), int(response.group(2))
        else:
            return False, False

    @http.route('/bryntum_gantt_enterprise/send/update',
                method='POST', type='json', auth='user')
    def bryntum_gantt_update(self, data=None, **kw):
        data_json = loads(data)
        task_env = request.env['project.task']
        project_env = request.env['project.project']
        task_linked_env = request.env['project.task.linked']

        for el in data_json:
            gantt_model_id = el['model']['id']
            model, int_id = self.gantt_id(gantt_model_id)

            if not int_id:
                continue

            new_data = el.get('newData', {})

            if model == 'project-task':
                task = task_env.search([('id', '=', int_id)])
                task_gantt_ids = new_data.get('taskLinks')

                if not task_gantt_ids is None:
                    task.linked_ids.unlink()
                    for link in task_gantt_ids:
                        task_linked_env.create({
                            'from_id': self.to_id(link.get('from')),
                            'to_id': self.to_id(link.get('to'))
                        })

                data = self.field_related(new_data, self.default_fields)

                task.write(data)
            elif model in ('project', 'project-project'):
                project = project_env.search([('id', '=', int_id)])
                start_date = new_data.get('startDate')
                if project and start_date:
                    project.write({
                        'project_start_date': self.from_gantt_date(start_date)
                    })

        return {'status': 'updated'}

    @http.route('/bryntum_gantt_enterprise/send/remove',
                method='POST', type='json', auth='user')
    def bryntum_gantt_remove(self, data=None, **kw):
        data_json = loads(data)
        task_env = request.env['project.task']

        task_gantt_ids = [item for outer in data_json for item in outer]
        task_int_ids = [self.to_id(el) for el in task_gantt_ids]

        task = task_env.search([('id', 'in', task_int_ids)])
        task.unlink()

        return {'status': 'deleted'}

    @http.route('/bryntum_gantt_enterprise/send/create',
                method='POST', type='json', auth='user')
    def bryntum_gantt_create(self, data=None, project_id=None, **kw):
        data_json = loads(data)
        task_env = request.env['project.task']
        create_int_ids = []

        for rec in data_json:
            if not self.is_gantt_new_id(rec.get('id')):
                continue
            data = self.field_related(rec, self.default_fields)
            data.update(project_id=project_id)
            task = task_env.create(data)
            create_int_ids.append((rec.get('id'),
                                   self.task_id_template % task.id))

        return {
            'status': 'created',
            'ids': create_int_ids
        }
