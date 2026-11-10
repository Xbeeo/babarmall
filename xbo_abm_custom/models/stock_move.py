# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockMoveInherit(models.Model):
    _inherit = 'stock.move'
    _description = 'Stock Move Inherit'

    qty_available = fields.Float(string='Qty Available', related='product_id.qty_available', store=True, readonly=True)
    total_pcs = fields.Float(string='Total Pcs', compute='_compute_total_pcs')
    last_order_date = fields.Datetime(string="Last Date", compute='_compute_last_order')
    last_order_rate = fields.Float(string="Last Rate", compute='_compute_last_order')
    last_order_ref = fields.Char(string="Last PO/SO", compute='_compute_last_order')

    @api.depends('product_id', 'picking_id.partner_id', 'picking_id.picking_type_code')
    def _compute_last_order(self):
        for move in self:
            move.last_order_date = False
            move.last_order_rate = 0.0
            move.last_order_ref = False
            partner = move.picking_id.partner_id
            if not partner or not move.product_id:
                continue
            code = move.picking_id.picking_type_code
            if code == 'incoming':
                model, current = 'purchase.order.line', move.purchase_line_id.order_id
            elif code == 'outgoing':
                model, current = 'sale.order.line', move.sale_line_id.order_id
            else:
                continue
            domain = [
                ('order_id.partner_id', '=', partner.id),
                ('product_id', '=', move.product_id.id),
                ('order_id.state', 'not in', ['draft', 'sent', 'cancel']),
            ]
            if current:
                domain.append(('order_id', '!=', current.id))
            line = self.env[model].search(
                domain, order='create_date desc, id desc', limit=1)
            if line:
                move.last_order_date = line.order_id.date_order
                move.last_order_rate = line.price_unit
                move.last_order_ref = line.order_id.name

    @api.depends('product_uom_qty', 'product_uom')
    def _compute_total_pcs(self):
        for move in self:
            if move.product_uom_qty and move.product_uom:
                move.total_pcs = move.product_uom_qty * move.product_uom.relative_factor
            else:
                move.total_pcs = 0.0
