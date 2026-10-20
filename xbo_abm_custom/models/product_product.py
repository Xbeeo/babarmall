# -*- coding: utf-8 -*-

from odoo import fields, models ,api, _
from odoo.osv import expression


class ProductVariantInherit(models.Model):
    _inherit = 'product.product'

    partner_id = fields.Many2one(comodel_name='res.partner', string='Vendor',related='product_tmpl_id.partner_id', store=True)
    floor_id = fields.Many2one(comodel_name='floor.product', string='Floor',related='product_tmpl_id.floor_id', store=True)
    brand_id = fields.Many2one(comodel_name='brand.brand', string='Brand',related='product_tmpl_id.brand_id', store=True)
    color_id = fields.Many2one(comodel_name='color.color', string='Color',related='product_tmpl_id.color_id', store=True)
    size_id =  fields.Many2one(comodel_name='size.size', string='Size',related='product_tmpl_id.size_id', store=True)
    seasons_id = fields.Many2one(comodel_name='seasons.seasons',related='product_tmpl_id.seasons_id', store=True)
    margin_percentage = fields.Float(
        string='Margin %',related='product_tmpl_id.margin_percentage', store=True
    )
    catalog_qty = fields.Float(
        string='Qty', compute='_compute_catalog_qty', inverse='_inverse_catalog_qty')

    def _get_catalog_line(self, order):
        self.ensure_one()
        return order.order_line.filtered(
            lambda l: l.product_id == self and not l.display_type)[:1]

    @api.depends_context('order_id')
    def _compute_catalog_qty(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        for product in self:
            line = product._get_catalog_line(order) if order else False
            product.catalog_qty = line.product_uom_qty if line else 0.0

    def _inverse_catalog_qty(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        if not order:
            return
        for product in self:
            line = product._get_catalog_line(order)
            if product.catalog_qty > 0:
                if line:
                    line.product_uom_qty = product.catalog_qty
                else:
                    order.write({'order_line': [(0, 0, {
                        'product_id': product.id,
                        'product_uom_qty': product.catalog_qty,
                    })]})
            elif line:
                line.unlink()

    @api.depends('brand_id', 'color_id', 'size_id')
    def _compute_display_name(self):
        super()._compute_display_name()
        for product in self:
            parts = [product.display_name]
            for field in ('brand_id', 'color_id', 'size_id'):
                value = product[field]
                if value:
                    parts.append(value.name)
            product.display_name = " - ".join(filter(None, parts))

    @api.model
    def name_search(
            self,
            name='',
            domain=None,
            operator='ilike',
            limit=100
    ):
        domain = domain or []

        if name:
            product_uoms = self.env['product.uom'].search([
                ('barcode', 'ilike', name),
            ])

            uom_product_ids = product_uoms.mapped(
                'product_id'
            ).ids

            search_domain = expression.OR([
                [('name', operator, name)],
                [('default_code', operator, name)],
                [('barcode', operator, name)],
                [('id', 'in', uom_product_ids)],
            ])

            products = self.search(
                expression.AND([
                    domain,
                    search_domain,
                ]),
                limit=limit
            )

            return [
                (product.id, product.display_name)
                for product in products
            ]

        products = self.search(
            domain,
            limit=limit
        )

        return [
            (product.id, product.display_name)
            for product in products
        ]
