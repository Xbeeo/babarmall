# -*- coding: utf-8 -*-

from odoo import api, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def add_product_by_barcode(self, picking_id, barcode):

        picking = self.browse(picking_id)

        product_uom = self.env["product.uom"].search([
            ("barcode", "=", barcode)
        ], limit=1)

        if not product_uom:
            return {
                "success": False,
                "message": "Product not found for barcode: %s" % barcode,
            }

        move = picking.move_ids.filtered(
            lambda m:
                m.product_id == product_uom.product_id
                and m.product_uom == product_uom.uom_id
        )[:1]

        if move:

            move.product_uom_qty += (
                product_uom.uom_id.relative_factor
            )

            line_id = move.id

        else:

            new_move = self.env["stock.move"].create({
                "picking_id": picking.id,
                "product_id": product_uom.product_id.id,
                "product_uom": product_uom.uom_id.id,
                "product_uom_qty": product_uom.uom_id.relative_factor,
            })

            line_id = new_move.id

        return {
            "success": True,
            "product_id": product_uom.product_id.id,
            "name": product_uom.product_id.display_name,
            "line_id": line_id,
        }