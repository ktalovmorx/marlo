# -*- coding: utf-8 -*-
{
    'name': "MarloPos",
    'summary': "Extensión del modulo POS para ver comandas en cocina",
    'description': """
        Muestra de comandas en la cocina
    """,
    'author': "Cristina Marzo Lopez",
    'website': "",
    'category': 'Accounting',
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['base', 'point_of_sale', 'pos_restaurant', 'marlo_sn'],
    'data': [
        'security/ir.model.access.csv',
        'views/actions/templates.xml',
        'views/searchs/views.xml',
        'views/inherits/views.xml',
        'views/paper_formats/templates.xml',
        'views/reports/templates.xml',
        'views/views.xml',
        'views/templates.xml'
    ],
    'assets': {
        'point_of_sale.assets_prod': [
            'pos_sn/static/src/css/styles.css',
        ]
    },
    'installable': True,
    'application': True,
}

