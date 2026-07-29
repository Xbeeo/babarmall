# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class ProductUom(models.Model):
    _inherit = 'product.uom'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('barcode'):
                vals['barcode'] = self.env['ir.sequence'].next_by_code('bmp.sequence')
        return super().create(vals_list)