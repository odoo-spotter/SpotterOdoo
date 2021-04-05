# -*- coding: utf-8 -*-
{
    'name': "Bohm Customizations",
    'summary': """Odoo customizations from Bohm Technologies""",
    'description': """
		Bohm Technologies Customizations
	""",
    'author': "Bohm Technologies",
    'website': "https://www.bohmtechnologies.com",
    'category': 'Uncategorized',
    'version': '1.0',
    'depends': ['repair'],
    'data': [
        'security/ir.model.access.csv',
        'views/repair_order_form.xml',
        'views/crm_lead_form.xml',
        'views/helpdesk_ticket_form.xml',
        'views/assets.xml',
        'views/documents_document_form.xml'
    ],
    'application': True,
}
