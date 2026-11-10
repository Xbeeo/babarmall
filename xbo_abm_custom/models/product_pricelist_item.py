# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    percent_price = fields.Float(string='Disc. %')
    discount_amount = fields.Float(string='Disc. Amt')
    product_tmpl_ids = fields.Many2many(
        comodel_name='product.template',
        string="Products",
        store=False,
        help="Select multiple products; one rule will be created per product.")

    @api.onchange('product_tmpl_ids')
    def _onchange_product_tmpl_ids(self):
        if self.product_tmpl_ids:
            self.product_tmpl_id = self.product_tmpl_ids[:1]

    @api.onchange('percent_price')
    def _onchange_percent_price_discount(self):
        if self.percent_price:
            self.discount_amount = 0

    @api.onchange('discount_amount')
    def _onchange_discount_amount_discount(self):
        if self.discount_amount:
            self.percent_price = 0

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            values.pop('product_tmpl_ids', None)  # defensive cleanup for non-UI create calls
            self._sync_discount_fields(values)
        records = super().create(vals_list)
        records._replace_previous_lines()
        return records

    def write(self, vals):
        self._sync_discount_fields(vals)
        res = super().write(vals)
        if {'product_tmpl_id', 'pricelist_id', 'percent_price',
                'discount_amount', 'fixed_price'} & set(vals):
            self._replace_previous_lines()
        return res

    def _replace_previous_lines(self):
        for rec in self:
            if not rec.pricelist_id or not rec.product_tmpl_id:
                continue
            older = self.search([
                ('pricelist_id', '=', rec.pricelist_id.id),
                ('product_tmpl_id', '=', rec.product_tmpl_id.id),
                ('id', '<', rec.id),
            ])
            for old in older:
                for fname in ('percent_price', 'discount_amount', 'fixed_price'):
                    if rec[fname] and rec[fname] == old[fname]:
                        raise ValidationError(_(
                            "Product %(product)s already has a line with the same %(field)s (%(value)s).",
                            product=rec.product_tmpl_id.display_name,
                            field=rec._fields[fname].string,
                            value=rec[fname],
                        ))
            older.unlink()

    @api.model
    def _sync_discount_fields(self, vals):
        if vals.get('discount_amount'):
            vals['percent_price'] = 0
        elif vals.get('percent_price'):
            vals['discount_amount'] = 0

    def _compute_price(self, product, quantity, uom, date, currency=None, **kwargs):
        price = super()._compute_price(product, quantity, uom, date, currency=currency, **kwargs)
        if self and self.compute_price == 'percentage' and self.discount_amount:
            base_price = self._compute_base_price(
                product, quantity, uom, date,
                currency or self.currency_id or self.env.company.currency_id, **kwargs)
            price = base_price - self.discount_amount
        return price

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