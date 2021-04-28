# -*- coding: utf-8 -*-

{
    "name": "Project Templates",
    "summary": "Generate projects from a pre-configurated templates",
    "author": "Solux Software Development",
    "website": "solux.pe",
    "category": "Operations/Project",
    "version": "13.0.1.0.0",
    "license": "OPL-1",
    'price': 59.0,
    'currency': 'EUR',
    "depends": ["project"],    
    "installable": True,
    'application': False,

    'data': [
        "wizard/project_from_template.xml",
        "views/project_template_views.xml",
        "views/project_views.xml",
        "views/webclient_templates.xml",
        "security/ir.model.access.csv"
        ],
    
    'qweb': [
        "static/src/xml/create_from_template_button.xml",
    ],

    'images': [
        'static/description/main.png',
    ],

}