# -*- coding: utf-8 -*-
{
    "name": "Xbo Abm Report",

    'version': '19.0.0.0',

    'summary': """Xbo Abm Report""",

    'description': """Xbo Abm Report""",

    'category': 'report',

    'author': "Xbeeo",

    'website': 'https://xbeeo.com/',

    "depends": ['base', 'xbo_abm_custom', 'accounting_pdf_reports'],

    "data": [
        'security/ir.model.access.csv',
        'report/product_packaging.xml',
        'report/report_templates.xml',
        'report/action_report.xml',
        'report/custom_sale_order_template.xml',
        'report/custom_invoice_report_templ.xml',
        'report/custom_credit_note_report_template.xml',
        'report/trial_balance_report_inherit.xml',
        'report/custom_purchase_order.xml',
        'wizards/bad_debt_wizard_views.xml',
        'wizards/uom_line_print_wizard_views.xml',
        'views/product_template_uom_line_views.xml',
        'report/bad_debt_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'xbo_abm_report/static/src/js/bad_debt_list.js',
            'xbo_abm_report/static/src/xml/bad_debt_list.xml',
        ],

    }
}