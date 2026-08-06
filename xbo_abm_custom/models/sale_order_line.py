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
    total_pcs = fields.Float(
        string='Total Pcs',
        compute='_compute_total_pcs',
    )

    custom_unit_price = fields.Float(string="Unit Price")

    @api.onchange('product_id')
    def _onchange_product_id_custom(self):
        for line in self:
            if line.product_template_id:
                template = line.product_template_id

                parts = [
                    template.brand_id.name if template.brand_id else "",
                    template.color_id.name if template.color_id else "",
                    template.size_id.name if template.size_id else "",
                    template.seasons_id.name if template.seasons_id else "",
                ]

                line.name = " - ".join(filter(None, parts))
                line.custom_unit_price = line.product_id.lst_price

    @api.depends('product_uom_qty','product_uom_id')
    def _compute_total_pcs(self):
        for line in self:
            if line.product_uom_qty  and line.product_uom_id:
                line.total_pcs = line.product_uom_qty * line.product_uom_id.relative_factor
            else:
                line.total_pcs = 0


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

    def _update_discount_amount(self):
        for line in self:
            total = line.price_unit * line.product_uom_qty
            line.discount_amount = (total * line.discount) / 100 if total else 0.0

    @api.onchange('discount_amount', 'price_unit', 'product_uom_qty')
    def discount_amount_onchange(self):
        if self.discount_amount:
            amt = self.price_unit * self.product_uom_qty
            pis_p = (self.discount_amount / amt) * 100
            self.discount = pis_p
        else:
            self.discount = 0

    # @api.onchange('discount')
    # def discount_p_onchange(self):
    #     if self.discount:
    #         amt = self.price_unit * self.product_uom_qty
    #         pis_p = (amt / 100) * self.discount
    #         self.discount_amount = pis_p
    #     else:
    #         self.discount_amount = 0
    @api.onchange('discount')
    def discount_p_onchange(self):
        self._update_discount_amount()

    def _prepare_invoice_line(self, **optional_values):
        res = super()._prepare_invoice_line(**optional_values)
        res.update({
            'discount_amount': self.discount_amount or 0.0,
        })
        return res

    def write(self, vals):
        res = super().write(vals)

        if any(k in vals for k in ('discount', 'price_unit', 'product_uom_qty')):
            self._update_discount_amount()

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