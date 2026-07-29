# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.tools import float_compare


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def action_open_warehouse_wizard(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Product Warehouses',
            'res_model': 'warehouse.selection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.product_id.id,
                'default_partner_id': self.order_id.partner_id.id,
                'default_move_type' :'in_invoice'
            }
        }