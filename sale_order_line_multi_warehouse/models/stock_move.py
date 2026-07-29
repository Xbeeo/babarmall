# -*- coding: utf-8 -*-

from odoo import fields, models , api
from odoo.exceptions import UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    picking_code = fields.Selection(
        related='picking_type_id.code',
        store=True
    )

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
                'default_partner_id': self.picking_id.partner_id.id,
                'default_move_type' :'internal'
            }
        }