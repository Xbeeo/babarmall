# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    vendor_id = fields.Many2one(comodel_name='res.partner',string='Vendor',related='product_id.partner_id', store=True)