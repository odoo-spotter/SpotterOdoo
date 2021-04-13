# -*- coding: utf-8 -*-

from odoo import models, fields


class CustomProject(models.Model):
    _inherit = 'project.task'
    check_box = fields.Boolean(string='Is Check List', default=False)
    info_checklist = fields.One2many(comodel_name="check.list", inverse_name="name", required=True,
                                     track_visibility='onchange')
    progress_rate = fields.Integer(string='Checklist Progress', compute="check_rate")
    total = fields.Integer(string="Max")
    status = fields.Selection(string="Status",
                              selection=[('done', 'Done'), ('progress', 'In Progress'), ('cancel', 'Cancel')],
                              readonly=True, track_visibility='onchange')

    maximum_rate = fields.Integer(default=100)

    def check_rate(self):
        for rec in self:
            rec.progress_rate = 0
            total = len(rec.info_checklist.ids)
            done = 0
            cancel = 0
            # message = 'Create Work!'
            if total == 0:
                pass
            else:
                if rec.info_checklist:
                    for item in rec.info_checklist:
                        if item.status == 'done':
                            done += 1
                            # message = "Work: %s <br> Status: done" % (item.name_work)
                        if item.status == 'cancel':
                            cancel += 1
                            # message = "Work: %s <br> Status: cancel" % (item.name_work)
                        # if item.status == 'progress':
                        #     message = "Work: %s <br> Status: In Progress" % (item.name_work)
                    if cancel == total:
                        rec.progress_rate = 0
                    else:
                        rec.progress_rate = round(done / (total - cancel), 2) * 100
            # rec.message_post(body=message)
