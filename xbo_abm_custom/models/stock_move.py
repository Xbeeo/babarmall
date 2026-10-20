# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockMoveInherit(models.Model):
    _inherit = 'stock.move'
    _description = 'Stock Move Inherit'

    qty_available = fields.Float(string='Qty Available', related='product_id.qty_available', store=True, readonly=True)
    total_pcs = fields.Float(string='Total Pcs', compute='_compute_total_pcs')

    @api.depends('product_uom_qty', 'product_uom')
    def _compute_total_pcs(self):
        for move in self:
            if move.product_uom_qty and move.product_uom:
                move.total_pcs = move.product_uom_qty * move.product_uom.relative_factor
            else:
                move.total_pcs = 0.0
