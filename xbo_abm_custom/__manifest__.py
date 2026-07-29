# -*- coding: utf-8 -*-
{
    "name": "Xbo ABm Custom",

    'version': '19.0.0.0',

    'summary': """Xbo Abm Custom""",

    'description': """Xbo Abm Custom""",

    'category': 'custom',

    'author': "Xbeeo",

    'website': 'https://xbeeo.com/',

    "depends": ['base','sale_management','account','purchase','stock','contacts','hr'],

    "data": [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence_data.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'views/purchase_order_views.xml',
        'views/stock_picking_views.xml',
        'views/city_city_views.xml',
        'views/party_type_views.xml',
        'views/product_template_views.xml',
        'views/product_product_views.xml',
        'views/floor_wise_product_views.xml',
        'views/brand_brand_views.xml',
        'views/color_color_views.xml',
        'views/seasons_seasons_views.xml',
        'views/product_pricelist_item_views.xml',
        'views/size_size_views.xml',
        'views/res_users_views.xml',
    ],

}
