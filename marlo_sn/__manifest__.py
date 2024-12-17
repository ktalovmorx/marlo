# -*- coding: utf-8 -*-
{
    'name': "BaseMarlo",
    'summary': "Gestion de Restaurantes",
    'description': """
        La gestión de un restaurante, es una aplicación
        web que busca el equilibrio entre calidad,
        eficiencia y rentabilidad del negocio.
        El objetivo principal es gestionar los diferentes
        departamentos como, operacionales, de
        inventario, financieros y atención al cliente.
    """,
    'author': "Cristina Marzo Lopez",
    'website': "",
    'category': 'Accounting',
    'version': '1.9',
    'license': 'LGPL-3',
    'depends': ['base', 'contacts', 'calendar', 'owl_dashboard_sn',
                'hr_expense', 'hr_holidays', 'hr_recruitment', 'hr_contract', 'hr_attendance',
                'hr_holidays_attendance', 'hr_maintenance', 'sale', 'purchase',
                'stock', 'mrp', 'board', 'payment_stripe', 'base_geolocalize', 'bus', 'calendar',
                'crm'],
    'data': [
        'security/ir.model.access.csv',
        'views/searchs/views.xml',
        'views/actions/templates.xml',
        'views/inherits/views.xml',
        'views/paper_formats/templates.xml',
        'views/reports/templates.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'marlo_sn/static/src/css/login_style.scss',
        ]
    },
    'installable': True,
    'application': True,
}

