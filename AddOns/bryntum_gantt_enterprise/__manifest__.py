# -*- coding: utf-8 -*-
{
    'name': "Gantt View PRO (Enterprise)",

    'summary': """
    Manage and visualise your projects with the fastest Gantt chart on the web.
    """,

    'description': """
    Bryntum Gantt chart is the most powerful Gantt component available. It has a massive set of features that will cover all your project management needs.
    """,

    'author': "Bryntum AB",
    'website': "https://www.bryntum.com/forum/viewforum.php?f=58",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '1.0',

    'price'   : 329.99,
    'currency': 'EUR',
    'license' : 'Other proprietary',

    'support' : 'odoosupport@bryntum.com',
    'live_test_url': 'https://odoo-gantt.bryntum.com',

    # any module necessary for this one to work correctly
    'depends': ['base', 'project', 'project_enterprise'],
    'images' : ['images/banner.png', 'images/main_screenshot.png','images/reschedule.gif'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/project_views.xml',
        'views/templates.xml',
    ],
    'application': True,
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
