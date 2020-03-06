# -*- coding: utf-8 -*-

{
    'name': 'Product Pricelists Excel Reports',
    "author": "Edge Technologies",
    'version': '13.0.1.0',
    'live_test_url': "https://youtu.be/hRVz22h4HiA",
    "images":['static/description/main_screenshot.png'],
    'summary': " This app helps you to print Product Pricelists Excel Reports.",
    'description': """ This app helps user to print Product Pricelists Excel Reports.
    				   User can print Product Pricelists Excel Report with different templates. 

print product pricelists
print pricelists reports Pricelists in Excel format Pricelists Excel format
print price list report Pricelists in MS Excel format (XLSX, XLSM)
pricelists reports pricelist reports excel pricelist reports
odoo pricelist reports
odoo product pricelist report pricelists xls reports
pricelists reports
pricelists xls reports

Professional Pricelists Excel (XLSX,XLSM)
Product Pricelists Excel Reports excel report for pricelist
product pricelist reports









    """,
    "license" : "OPL-1",
    'depends': ['base', 'sale_management','stock'],
    'data': [
            'security/ir.model.access.csv',
		    'data/pricelist_config_data.xml',
		    'views/pricelist_excel_config.xml',
		    'wizard/product_price_list_views.xml',
            ],
    'installable': True,
    'auto_install': False,
    'price': 88,
    'currency': "EUR",
    'category': 'Sales',
    
}

