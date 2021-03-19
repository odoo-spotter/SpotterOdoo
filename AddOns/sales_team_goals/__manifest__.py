# -*- coding: utf-8 -*-
{
    'name': "Sales Team Goals",

    'summary': """
        Sales Team Goals""",

    'description': """
        Added Ability to add Sales Teams Goals and Dashboard
    """,

    'author': "Bohm Technologies",
    'website': "https://www.bohmtechnologies.com",
    'category': 'Sales',
    'version': '0.1',
    'depends': ['base', 'sale', 'crm', 'repair'],
    'data': [
        'security/ir.model.access.csv',
        'views/sales_dashboard.xml',
        'views/crm_team_form.xml'
    ]
}
