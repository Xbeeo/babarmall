# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class SaleOrderline(models.Model):
    _inherit = 'sale.order.line'

    discount_amount = fields.Float(string='Disc Amount')
    discount = fields.Float( string="Discount (%)", digits=(16, 6), default=0.0 )

    allowed_product_ids = fields.Many2many(
        comodel_name='product.product',
        compute='_compute_allowed_products',
        string='Allowed Products'
    )

    sr_no = fields.Integer(
        string='Sr#',
        compute='_compute_sr_no',
        store=False
    )

    @api.depends('order_id.order_line')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            sr = 1
            for line in order.order_line.sorted('sequence'):
                line.sr_no = sr
                sr += 1

    item_code = fields.Char(
        string='Item Code',
        related='product_id.barcode',
        store=True,
        readonly=True
    )

    def _compute_allowed_products(self):
        for line in self:
            locations = self.env.user.allowed_location_id

            if locations:
                quants = self.env['stock.quant'].search([
                    ('location_id', 'in', locations.ids),
                    ('quantity', '>', 0),
                ])

                line.allowed_product_ids = quants.mapped('product_id')
            else:
                line.allowed_product_ids = self.env['product.product'].search([])

    can_edit_discount = fields.Boolean(
        compute="_compute_can_edit_discount"
    )

    def _compute_can_edit_discount(self):
        for line in self:
            line.can_edit_discount = self.env.user.has_group(
                'xbo_abm_custom.group_allow_sale_discount_conf_menu_access'
            )

    @api.onchange('discount_amount', 'price_unit', 'product_qty')
    def discount_amount_onchange(self):
        if self.discount_amount:
            amt = self.price_unit * self.product_uom_qty
            pis_p = (self.discount_amount / amt) * 100
            self.discount = pis_p
        else:
            self.discount = 0

    @api.onchange('discount')
    def discount_p_onchange(self):
        if self.discount:
            amt = self.price_unit * self.product_uom_qty
            pis_p = (amt / 100) * self.discount
            self.discount_amount = pis_p
        else:
            self.discount_amount = 0

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            'discount_amount': self.discount_amount or 0.0,
        })
        return res

    @api.depends('product_template_id', 'product_uom_qty', 'product_uom_id','pricelist_item_id','price_unit')
    def _compute_discount(self):
        super()._compute_discount()

        for line in self:
            if not line.product_template_id or not line.pricelist_item_id:
                continue

            # Case 1: Discount Amount from Pricelist
            if line.pricelist_item_id.discount_amount:
                line.discount_amount = line.pricelist_item_id.discount_amount

                total = line.price_unit * line.product_uom_qty
                if total:
                    line.discount = (line.discount_amount / total) * 100

            # Case 2: Percentage Discount from Pricelist
            else:
                total = line.price_unit * line.product_uom_qty
                line.discount_amount = (total * line.discount) / 100