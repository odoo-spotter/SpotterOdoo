# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'Generic Rental Management for all types',
    'version' : '1.0',
    'author' : 'Globalteckz',
    'category' : 'Extra Tools',
    'description' : """
rental
generic rental
rental management
generic rental management
car rental
fleet
fleet rental
rental car
rental dress
rental machine
rental machineary
hire machineary
machineary rental
car rental
dress rental
machine rental
machineary rental
recurring rental
rent car
car rent
rent a car
car a rent
rental
odoo rental management
management rent
management rental
""",
    'website': 'https://www.globalteckz.com',
    'images': ['static/description/Banner.png'],
    "price": "99.00",
    "currency": "EUR",
    "license" : "Other proprietary",
    'summary': "This app will help for rent the products like car, electronic accessories, machineary etc.. its generic so can be used for any rental business",
    'depends' : ['sale_management','stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/ir_sequence_data.xml',
        'wizard/rental_wizard.xml',
        'report/rental.xml',
        'views/rental_product.xml',
        'views/res_config.xml',
    ],
    'qweb' : [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
