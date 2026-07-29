# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    partner_current_balance = fields.Monetary(string="Current Balance", compute='_compute_partner_current_balance')
    product_catg_id = fields.Many2one(comodel_name='product.category', string="Product Category")

    total_before_dis = fields.Float(
        string="Total Before Discount",
        compute="_compute_total_before_dic",
        store=True,
    )

    total_discount = fields.Float(
        string="Total Discount",
        compute="_compute_total_discount",
        store=True,
    )

    @api.depends('order_line.discount_amount')
    def _compute_total_discount(self):
        for move in self:
            total = 0.0
            for line in move.order_line:
                total += line.discount_amount
            move.total_discount = total

    @api.depends('order_line.product_qty', 'order_line.price_unit')
    def _compute_total_before_dic(self):
        for move in self:
            total = 0.0
            for line in move.order_line:
                total += line.product_uom_qty * line.price_unit
            move.total_before_dis = total

    """COMPUTE PARTNER CURRENT BALANCE"""

    @api.depends('partner_id')
    def _compute_partner_current_balance(self):
        for rec in self:
            if rec.partner_id:
                rec.partner_current_balance = rec.partner_id.credit - rec.partner_id.debit
            else:
                rec.partner_current_balance = False

    def _prepare_invoice(self):
        invoice_vals = super(PurchaseOrderInherit, self)._prepare_invoice()
        invoice_vals['product_catg_id'] = self.product_catg_id.id

        return invoice_vals