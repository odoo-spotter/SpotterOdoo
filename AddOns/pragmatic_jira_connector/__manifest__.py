{
    'name': 'Odoo Jira Connector',
    'version': '13.0.2',
    'author': 'Pragmatic TechSoft Pvt Ltd.',
    'website': 'http://www.pragtech.co.in',
    'category': 'Project',
    'summary': 'Synchronise data between Odoo and Jira odoo jira odoo connector jira connector odoo task bug jira task issue ',
    'description': """
    Odoo Jira Connector
    =======================================
    
    This connector will help user to import/export following objects in Jira.
    * Project
    * Task (Issues)
    * user
    * Attachments
    * Messages
    <keywords>
odoo jira odoo connector jira connector odoo task bug jira task issue
    """,
    'depends': ['project','hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/project_views.xml',
        'views/res_company_views.xml',
        'wizards/message_view.xml'
    ],
    'images': ['image/Animated-Jira-connector.gif'],
    'price': 99,
    'currency': 'EUR',
    'license': 'OPL-1',
    'auto_install': False,
    'application': False,
    'installable': True,
}
