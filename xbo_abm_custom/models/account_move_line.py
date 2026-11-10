# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    discount_amount = fields.Float(string='Disc Amount')
    discount = fields.Float(string="Discount (%)", digits=(16, 6), default=0.0)

    can_edit_discount = fields.Boolean(
        compute="_compute_can_edit_discount"
    )

    pricelist_item_id = fields.Many2one(
        'product.pricelist.item', string='Pricelist Rule', copy=False
    )

    def _compute_can_edit_discount(self):
        for line in self:
            line.can_edit_discount = self.env.user.has_group(
                'xbo_abm_custom.group_allow_sale_discount_conf_menu_access'
            )

    @api.onchange('discount_amount', 'price_unit', 'quantity')
    def discount_amount_onchange(self):
        if self.discount_amount:
            amt = self.price_unit * self.quantity
            self.discount = (self.discount_amount / amt) * 100 if amt else 0
        else:
            self.discount = 0

    @api.onchange('discount')
    def discount_p_onchange(self):
        if self.discount:
            amt = self.price_unit * self.quantity
            self.discount_amount = (amt / 100) * self.discount
        else:
            self.discount_amount = 0

    def _compute_discount_amount_from_pricelist(self):
        for line in self:
            item = line.pricelist_item_id
            if not line.product_id or not item:
                continue
            total = line.price_unit * line.quantity
            if item.discount_amount:
                line.discount_amount = item.discount_amount * (
                    line.quantity if item.compute_price == 'percentage' else 1)
                line.discount = (line.discount_amount / total) * 100 if total else 0
            else:
                line.discount = item.percent_price
                line.discount_amount = total * item.percent_price / 100

    def _apply_pricelist(self):
        for line in self:
            move = line.move_id
            if not (move.move_type == 'out_refund' and move.pricelist_id
                    and line.display_type == 'product' and line.product_id):
                continue
            pricelist = move.pricelist_id
            qty = line.quantity or 1.0
            date = move.invoice_date or fields.Date.today()
            rule_id = pricelist._get_product_rule(
                line.product_id, qty, uom=line.product_uom_id, date=date)
            item = self.env['product.pricelist.item'].browse(
                getattr(rule_id, 'id', rule_id) or [])
            line.pricelist_item_id = item.id or False
            if not item:
                line.discount = 0
                line.discount_amount = 0
            if item and item.compute_price == 'percentage':
                # keep the base price, show the discount in the discount columns
                line.price_unit = item._compute_base_price(
                    line.product_id, qty, line.product_uom_id, date,
                    move.currency_id)
            else:
                line.price_unit = pricelist._get_product_price(
                    line.product_id, qty, uom=line.product_uom_id, date=date)
            line._compute_discount_amount_from_pricelist()

    @api.depends('product_id', 'product_uom_id', 'quantity', 'move_id.pricelist_id')
    def _compute_price_unit(self):
        super()._compute_price_unit()
        self._apply_pricelist()
