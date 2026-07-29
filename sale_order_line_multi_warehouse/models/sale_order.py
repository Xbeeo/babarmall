# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    """
        Extension of 'sale.order.line' with an additional
        field 'product_warehouse_id'.
        """
    _inherit = 'sale.order.line'

    warehouse_location_ids = fields.Many2many(
        'stock.location',
        string="Warehouses"
    )

    # def _action_launch_stock_rule(self, *, previous_product_uom_qty=False):
    #
    #     if self.env.context.get("skip_procurement"):
    #         return True
    #
    #     precision = self.env['decimal.precision'].precision_get('Product Unit')
    #
    #     procurements = []
    #
    #     for line in self:
    #
    #         line = line.with_company(line.company_id)
    #
    #         if (
    #                 line.state != 'sale'
    #                 or line.order_id.locked
    #                 or line.product_id.type != 'consu'
    #         ):
    #             continue
    #
    #         qty = line._get_qty_procurement(
    #             previous_product_uom_qty
    #         )
    #
    #         if float_compare(
    #                 qty,
    #                 line.product_uom_qty,
    #                 precision_digits=precision
    #         ) == 0:
    #             continue
    #
    #         references = line.order_id.stock_reference_ids
    #
    #         if not references:
    #             self.env['stock.reference'].create(
    #                 line._prepare_reference_vals()
    #             )
    #
    #         remaining_qty = line.product_uom_qty - qty
    #
    #         locations = line.warehouse_location_ids
    #
    #         # agar location select nahi ki
    #         if not locations:
    #
    #             values = line._prepare_procurement_values()
    #
    #             product_qty, procurement_uom = (
    #                 line.product_uom_id._adjust_uom_quantities(
    #                     remaining_qty,
    #                     line.product_id.uom_id
    #                 )
    #             )
    #
    #             procurements += line._create_procurements(
    #                 product_qty,
    #                 procurement_uom,
    #                 values
    #             )
    #
    #
    #         else:
    #
    #             for location in locations:
    #
    #                 if remaining_qty <= 0:
    #                     break
    #
    #                 available_qty = self.env['stock.quant']._get_available_quantity(
    #                     line.product_id,
    #                     location
    #                 )
    #
    #                 if available_qty <= 0:
    #                     continue
    #
    #                 take_qty = min(
    #                     available_qty,
    #                     remaining_qty
    #                 )
    #
    #                 values = line._prepare_procurement_values()
    #
    #                 values.update({
    #                     'source_location_id': location.id,
    #                     'group_id': False,
    #                 })
    #
    #                 product_qty, procurement_uom = (
    #                     line.product_uom_id._adjust_uom_quantities(
    #                         take_qty,
    #                         line.product_id.uom_id
    #                     )
    #                 )
    #
    #                 procurements += line._create_procurements(
    #                     product_qty,
    #                     procurement_uom,
    #                     values
    #                 )
    #
    #                 remaining_qty -= take_qty
    #
    #     if procurements:
    #         self.env['stock.rule'].run(procurements)
    #
    #     orders = self.mapped('order_id')
    #
    #     for order in orders:
    #
    #         pickings_to_confirm = order.picking_ids.filtered(
    #             lambda p: p.state not in ['cancel', 'done']
    #         )
    #
    #         if pickings_to_confirm:
    #             pickings_to_confirm.action_confirm()
    #
    #     return True

    def _prepare_procurement_values(self):
        values = super()._prepare_procurement_values()

        return values

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
                'default_move_type' :'out_invoice'
            }
        }