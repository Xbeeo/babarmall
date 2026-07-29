# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    discount_amount = fields.Float(string='Disc Amount')

    @api.depends(
        'compute_price',
        'fixed_price',
        'pricelist_id',
        'percent_price',
        'discount_amount',
        'price_discount',
        'price_markup',
        'price_surcharge',
        'base',
        'base_pricelist_id',
    )
    def _compute_price_label(self):
        super()._compute_price_label()

        for item in self:
            if item.compute_price == 'percentage' and item.discount_amount:
                if item.base_pricelist_id:
                    item.price = _(
                        "%(amount)s discount on %(pricelist)s",
                        amount=item.discount_amount,
                        pricelist=item.base_pricelist_id.display_name,
                    )
                else:
                    item.price = _(
                        "%(amount)s discount on sales price",
                        amount=item.discount_amount,
                    )

