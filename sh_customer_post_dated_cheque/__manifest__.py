# Copyright (C) Softhealer Technologies.
{
    "name": "Customer Post-Dated Cheque(PDC) Management",
    "author": "Cyngro",
    "website": "https://cyngro.com",
    "support": "https://cyngro.com",
    "category": "Accounting",
    "license": "OPL-1",
    "summary": "Customer Post Dated Cheque Management, Manage Post Dated Cheque, Supplier PDC,View VendorInvoice PDC App , List Of PDC Payment,Client PDC, Track PDC Process Module, Register Post Dated Cheque, Print PDC Report Odoo",
    "description": """In Invoice a post-dated cheque is a cheque written by the customer(payer) for a date in the future. Whether a post-dated cheque may be cashed or deposited before the date written on it depends on the country. Currently, odoo does not provide any kind of feature to manage post-dated cheque. That why we make this module. This module will help to manage a post-dated cheque. This module provides a button 'Register PDC Cheque' in invoice form view, after click button one 'PDC Payment' wizard will popup, you have must select a bank where you deposit a PDC cheque after register a PDC cheque you can see the list of PDC cheque payment list in the 'PDC Payment' menu. after register PDC Payment you can deposit or return that cheque. after deposit, if cheque bounced so you can set that payment on 'Bounced' state. You can track that process of PDC Payment in Bank 'General Ledger' as well as journal entries/items. also, print a PDF report of PDC Payment.

 Customer Post Dated Cheque Management Odoo
 Manage Client Post Dated Cheque Module, View Customer PDC In Invoice, See List Of PDC Payment Of Customer, Track PDC Process, Register Post Dated Cheque, Print PDC Report Odoo.
 Manage Post Dated Cheque, View Customer Invoice PDC App , List Of PDC Payment, Track PDC Process Module, Register Post Dated Cheque, Print PDC Report Odoo.
""",
    "version": "19.0.0.0",
    "depends": [
        "account"
    ],
    "data": [
        "data/ir_sequence.xml",
        # "data/account_data.xml",
        "data/ir_cron_data.xml",
        "data/mail_templates.xml",
        "security/ir.model.access.csv",
        "security/pdc_security.xml",
        "views/res_config_settings_views.xml",
        "wizard/pdc_payment_wizard_views.xml",
        "wizard/pdc_multi_action.xml",
        "views/account_move_views.xml",
        'report/pdc_payment_report.xml',
    ],

    "application": True,
    "auto_install": False,
    "installable": True,
    # "post_init_hook": "post_init_hook",
}
