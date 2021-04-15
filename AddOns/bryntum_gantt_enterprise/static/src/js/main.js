/*!
 *
 * Bryntum Gantt for Odoo 4.0.8
 * Copyright(c) 2021 Bryntum AB
 * https://bryntum.com/contact
 * https://bryntum.com/license
 *
 */
odoo.define('bryntum.gantt.widget', function (require) {
    "use strict";

    let view_registry = require('web.view_registry');
    let BasicView = require('web.BasicView');
    let BasicController = require('web.BasicController');
    let BasicRenderer = require('web.BasicRenderer');
    let ajax = require('web.ajax');

    let BryntumGanttController = BasicController.extend({
        start: function () {
            let response = this._super.apply(this, arguments);
            response.then(() => {
                this.$el.find('.o_cp_searchview, .o_search_options, .o_cp_pager, .o_cp_left').addClass('d-none');
                this.$el.find('.o_control_panel').addClass('d-flex justify-content-between');
                this.$el.find('.o_cp_controller .breadcrumb').parent().css('width', '100%');
                setTimeout(() => {
                    window.o_gantt.run = true;
                }, 100);
            });
            return response;
        }
    });

    let BryntumGanttRenderer = BasicRenderer.extend({
        init: function (parent, state, params) {
            this.state = state;
            return this._super.apply(this, arguments);
        },
        start: function () {
            let response = this._super.apply(this, arguments);
            let domain = this.state.domain ? this.state.domain.filter(el => el[0] === 'project_id') : [];

            this.$el.attr('id', 'bryntum-gantt');

            if (domain.length) {
                window.o_gantt.projectID = domain[0][2];
            }
            return response;
        },
        /**
         * @override
         */
        updateState: function (state, params) {
            let response = this._super.apply(this, arguments);

            window.o_gantt.update();

            let domain = this.state.domain ? this.state.domain.filter(el => el[0] === 'project_id') : [];

            if (domain.length) {
                this.state = state;
                window.o_gantt.projectID = domain[0][2];
            }

            return response;
        },
        destroy: function () {
            window.o_gantt.run = false;
            return this._super.apply(this, arguments);
        }
    });

    let BryntumGantt = BasicView.extend({
        display_name: 'Bryntum Gantt',
        icon: 'fa-th-list',
        viewType: 'BryntumGantt',
        jsLibs: [
            'bryntum_gantt_enterprise/static/gantt_src/js/app.js?v5.3',
            'bryntum_gantt_enterprise/static/gantt_src/js/chunk-vendors.js?v5.3'
        ],
        config: _.extend({}, BasicView.prototype.config, {
            Controller: BryntumGanttController,
            Renderer: BryntumGanttRenderer,
        })
    });

    view_registry.add('BryntumGantt', BryntumGantt);

    return {
        Gantt: BryntumGantt,
        Renderer: BryntumGanttRenderer,
        Controller: BryntumGanttController
    };
});
