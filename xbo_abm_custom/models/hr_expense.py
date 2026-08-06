# -*- coding: utf-8 -*-

from odoo import fields, models,api

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    payment_mode = fields.Selection(
        selection=[
            ('own_account', "Employee (to reimburse)"),
            ('company_account', "Company")
        ],
        string="Paid By",
        default='company_account',
        required=True,
        tracking=True,
    )
