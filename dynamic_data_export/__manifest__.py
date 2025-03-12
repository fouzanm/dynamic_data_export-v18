# -*- coding: utf-8 -*-
{
    'name': 'Dynamic Data Export',
    'version': '18.0.1.0.0',
    'summary': 'Export data to webhook endpoints',
    'category': 'Sales',
    'author': 'Fouzan M',
    'depends': ['base', 'web', 'sale' ],
    'data': [
        'security/ir.model.access.csv',
        'views/webhook_config_views.xml',
        'views/export_log_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
