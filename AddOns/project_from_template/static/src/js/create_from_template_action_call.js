odoo.define('project_from_template.template.kanban', function (require){
"use strict";
    
    var KanbanController = require('web.KanbanController');
    var KanbanView = require('web.KanbanView');
    var core = require('web.core');

    var _t = core._t;

    var viewRegistry = require('web.view_registry');

    function renderGenerateProjectFromTemplate() {
        if (this.$buttons) {
            var self = this;            
            this.$buttons.on('click', '.oe_create_project_from_template_action_button', function () {
                self.do_action({
                    type: "ir.actions.act_window",
                    name: _t("Create a Project from Template"),
                    res_model: "project.createfrom.template",                    
                    target: 'new',
                    views: [[false, 'form']],                     
                    flags: {'form': {'action_buttons': true, 'options': {'mode': 'edit'}}}
                });
            });
            
        }
    }

    var CreateProjectFromTemplateKanbanController = KanbanController.extend({
        willStart: function() {
            var self = this;
            var ready = this.getSession().user_has_group('project.group_project_manager')
                .then(function (is_project_manager) {
                    if (is_project_manager){
                        self.buttons_template = 'CreateProjectFromTemplate.buttons';                        
                    }
                });
            
            return Promise.all([this._super.apply(this, arguments), ready]);
        },
        renderButtons: function () {
            this._super.apply(this, arguments);
            renderGenerateProjectFromTemplate.apply(this, arguments);
        }
    });

    var CreateProjectFromTemplateKanbanView = KanbanView.extend({
        config: _.extend({}, KanbanView.prototype.config, {
            Controller: CreateProjectFromTemplateKanbanController,
        }),
    });

    viewRegistry.add('project_from_template_kanban', CreateProjectFromTemplateKanbanView);


});