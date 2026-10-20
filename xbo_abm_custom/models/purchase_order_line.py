# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    discount_amount = fields.Float(string='Disc Amount')
    discount = fields.Float( string="Discount (%)", digits=(16, 6), default=0.0 )
    sale_price = fields.Float(
        string='Sale Price',
        related='product_id.lst_price',
        store=True,
        readonly=True
    )
    margin_percentage = fields.Float(
        string='Margin %',
        related='product_id.margin_percentage',
        store=True,
        readonly=True
    )
    sr_no = fields.Integer(
        string='Sr#',
        compute='_compute_sr_no',
        store=False
    )

    item_code = fields.Char(
        string='Item Code',
        related='product_id.barcode',
        store=True,
        readonly=True
    )

    custom_unit_price = fields.Float(string="Unit Price")

    @api.onchange('product_id', 'product_uom_id')
    def _onchange_product_id_custom(self):
        for line in self:
            if line.product_id:
                product = line.product_id
                template = product.product_tmpl_id

                line.name = " - ".join(filter(None, [
                    template.brand_id.name if template.brand_id else "",
                    template.color_id.name if template.color_id else "",
                    template.size_id.name if template.size_id else "",

                    template.seasons_id.name if template.seasons_id else "",
                ]))

                line.custom_unit_price = product.standard_price

    @api.depends('order_id.order_line')
    def _compute_sr_no(self):
        for order in self.mapped('order_id'):
            sr = 1
            for line in order.order_line.sorted('sequence'):
                line.sr_no = sr
                sr += 1

    can_edit_discount = fields.Boolean(
        compute="_compute_can_edit_discount"
    )

    def _compute_can_edit_discount(self):
        for line in self:
            line.can_edit_discount = self.env.user.has_group(
                'xbo_abm_custom.group_allow_purchase_discount_conf_menu_access'
            )

    @api.onchange('discount_amount', 'price_unit', 'product_qty')
    def discount_amount_onchange(self):
        if self.discount_amount:
            amt = self.price_unit * self.product_qty
            pis_p = (self.discount_amount / amt) * 100
            self.discount = pis_p
        else:
            self.discount = 0

    @api.onchange('discount')
    def discount_p_onchange(self):
        if self.discount:
            amt = self.price_unit * self.product_qty
            pis_p = (amt / 100) * self.discount
            self.discount_amount = pis_p
        else:
            self.discount_amount = 0

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move)
        res.update({
            'discount_amount': self.discount_amount or 0.0,
        })
        return res