# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    discount_amount = fields.Float(string='Disc Amount')
    discount = fields.Float( string="Discount (%)", digits=(16, 6), default=0.0 )

    @api.onchange('discount_amount', 'price_unit', 'product_qty')
    def discount_amount_onchange(self):
        if self.discount_amount:
            amt = self.price_unit * self.quantity
            pis_p = (self.discount_amount / amt) * 100
            self.discount = pis_p
        else:
            self.discount = 0

    @api.onchange('discount')
    def discount_p_onchange(self):
        if self.discount:
            amt = self.price_unit * self.quantity
            pis_p = (amt / 100) * self.discount
            self.discount_amount = pis_p
        else:
            self.discount_amount = 0