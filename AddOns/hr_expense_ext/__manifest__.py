# -*- coding: utf-8 -*-
{
    'name': "HR Expense Extension",

    'summary': """
        Extend HR Expenses to allow creating Expense Records from Bank Statement Lines""",

    'description': """
        Extend HR Expenses to allow creating Expense Records from Bank Statement Lines.
        This module add a button to the Bank Statment Lines to auto create an expense record from bank data.
        Also, makes it posible to add expense product without changing unit price.
    """,

    'author': "Dream Mountain Services",
    'website': "https://dreammtn.services/",
    'category': 'Accounting/Expenses',
    'version': '0.1',
    'depends': ['hr_expense', 'account'],
    'data': [
        'views/account.xml',
    ]
}
