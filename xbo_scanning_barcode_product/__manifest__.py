# -*- coding: utf-8 -*-
{
    "name": "Xbo Barcode Product",

    'version': '19.0.0.0',

    'summary': """Xbo Barcode Product""",

    'description': """Xbo Barcode Product""",

    'category': 'Sales custom',

    'author': "Xbeeo",

    'website': 'https://xbeeo.com/',

    'depends': ['base', 'sale_management', 'web', 'stock','purchase','xbo_abm_custom'],

    "data": [
        # 'views/purchase_order_views.xml',
        # 'views/sale_order_view.xml',
    ],
    "assets": {
            "web.assets_backend": [
                "xbo_scanning_barcode_product/static/src/**/*",
            ],
        },

}
