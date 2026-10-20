# -*- coding: utf-8 -*-

from odoo import models, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def add_product_by_barcode(self, order_id, barcode):
        order = self.browse(order_id)

        product_uom = self.env["product.uom"].search([
            ("barcode", "=", barcode)
        ], limit=1)

        if not product_uom:
            return {
                "success": False,
                "message": "Product not found for barcode: %s" % barcode,
            }

        line = order.order_line.filtered(
            lambda l:
                l.product_id == product_uom.product_id
                and l.product_uom_id == product_uom.uom_id
        )

        if line:
            line.product_qty += 1
            line_id = line[0].id

        else:
            new_line = self.env["purchase.order.line"].create({
                "order_id": order.id,
                "product_id": product_uom.product_id.id,
                "name": " - ".join(filter(None, [
                    product_uom.product_id.product_tmpl_id.brand_id.name
                    if product_uom.product_id.product_tmpl_id.brand_id else "",
                    product_uom.product_id.product_tmpl_id.color_id.name
                    if product_uom.product_id.product_tmpl_id.color_id else "",
                    product_uom.product_id.product_tmpl_id.size_id.name
                    if product_uom.product_id.product_tmpl_id.size_id else "",
                    product_uom.product_id.product_tmpl_id.seasons_id.name
                    if product_uom.product_id.product_tmpl_id.seasons_id else "",
                ])),
                "product_qty": 1,
                "custom_unit_price": product_uom.product_id.standard_price,
                "product_uom_id": product_uom.uom_id.id,
            })

            line_id = new_line.id

        return {
            "success": True,
            "product_id": product_uom.product_id.id,
            "name": product_uom.product_id.display_name,
            "line_id": line_id,
        }