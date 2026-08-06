# -*- coding: utf-8 -*-

from odoo import models,fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.model
    def add_product_by_barcode(self, order_id, barcode):
        order = self.browse(order_id)

        product_uom = self.env["product.uom"].search([
            ("barcode", "=", barcode)
        ], limit=1)

        if not product_uom:
            return


        line = order.order_line.filtered(
            lambda l: l.product_id == product_uom.product_id and l.product_uom_id == product_uom.uom_id
        )

        if line:
            line.product_qty += 1
        else:
            self.env["purchase.order.line"].create({
                "order_id": order.id,
                "product_id": product_uom.product_id.id,
                "name": " - ".join(filter(None, [
                    product_uom.product_id.product_tmpl_id.brand_id.name if product_uom.product_id.product_tmpl_id.brand_id else "",
                    product_uom.product_id.product_tmpl_id.color_id.name if product_uom.product_id.product_tmpl_id.color_id else "",
                    product_uom.product_id.product_tmpl_id.size_id.name if product_uom.product_id.product_tmpl_id.size_id else "",

                    product_uom.product_id.product_tmpl_id.seasons_id.name if product_uom.product_id.product_tmpl_id.seasons_id else "",
                ])),
                "product_qty": 1,
                "custom_unit_price": product_uom.product_id.standard_price,
                "product_uom_id": product_uom.uom_id.id,
            })

        return {
            "product_id": product_uom.product_id.id,
            "name": product_uom.product_id.display_name,
        }

# class PurchaseOrderLine(models.Model):
#     _inherit = "purchase.order.line"
#
#     custom_unit_price = fields.Float(string="Unit Price")
#
#     @api.onchange('product_id', 'product_uom_id')
#     def _onchange_product_id_custom(self):
#         for line in self:
#             if line.product_id:
#                 product = line.product_id
#                 template = product.product_tmpl_id
#
#                 line.name = " - ".join(filter(None, [
#                     template.brand_id.name if template.brand_id else "",
#                     template.color_id.name if template.color_id else "",
#                     template.size_id.name if template.size_id else "",
#
#                     template.seasons_id.name if template.seasons_id else "",
#                 ]))
#
#                 line.custom_unit_price = product.standard_price