# -*- coding: utf-8 -*-
{
    "name": "Multiple Warehouse Locations in Sale Order Lines",

    'version': '19.0.0.0',

    'summary': """Multiple Warehouse Locations in Sale Order Lines""",

    'description': """Multiple Warehouse Locations in Sale Order Lines""",

    'category': 'Sales custom',

    'author': "Xbeeo",

    'website': 'https://xbeeo.com/',

    'depends': ['base', 'sale_management', 'account', 'stock','xbo_abm_custom'],

    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        # 'views/sale_order_view.xml',
        # 'views/purchase_order_views.xml',
        'views/stock_move_views.xml',
        'wizards/warehouse_selection_wizard_views.xml',
    ],

}
