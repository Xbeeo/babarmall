from odoo import models, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def add_product_by_barcode(self, order_id, barcode):

        order = self.browse(order_id).exists()

        if not order:
            return {
                "success": False,
                "message": "Sale Order not found.",
            }

        product_uom = self.env["product.uom"].search([
            ("barcode", "=", barcode)
        ], limit=1)

        if not product_uom:
            return {
                "success": False,
                "message": "Product not found for barcode: %s" % barcode,
            }

        product = product_uom.product_id

        # -------------------------------------------------
        # FIND EXISTING ORDER LINE
        # -------------------------------------------------

        line = order.order_line.filtered(
            lambda l:
                l.product_id == product
                and l.product_uom_id == product_uom.uom_id
        )[:1]

        # -------------------------------------------------
        # NEW QUANTITY
        # -------------------------------------------------

        new_qty = (
            line.product_uom_qty + 1
            if line
            else 1
        )

        # -------------------------------------------------
        # STOCK CHECK
        # -------------------------------------------------

        total_pcs = (
            new_qty *
            product_uom.uom_id.relative_factor
        )

        qty_available = product.free_qty

        if total_pcs > qty_available:

            return {
                "success": False,
                "message": (
                    "Cannot add product.\n\n"
                    "Product: %s\n"
                    "Required Pcs: %s\n"
                    "Available Pcs: %s"
                ) % (
                    product.display_name,
                    total_pcs,
                    qty_available,
                ),
            }

        # -------------------------------------------------
        # EXISTING LINE
        # -------------------------------------------------

        if line:

            line.product_uom_qty = new_qty

            line_id = line.id

        # -------------------------------------------------
        # NEW LINE
        # -------------------------------------------------

        else:

            obj_order = self.env["sale.order.line"].with_context(barcode_scan=True).create({

                "order_id": order.id,

                "product_id": product.id,

                "name": " - ".join(
                    filter(
                        None,
                        [

                            product.product_tmpl_id.brand_id.name
                            if product.product_tmpl_id.brand_id
                            else "",

                            product.product_tmpl_id.color_id.name
                            if product.product_tmpl_id.color_id
                            else "",

                            product.product_tmpl_id.size_id.name
                            if product.product_tmpl_id.size_id
                            else "",

                            product.product_tmpl_id.seasons_id.name
                            if product.product_tmpl_id.seasons_id
                            else "",
                        ]
                    )
                ),

                "product_uom_qty": 1,

                'item_code' : product.barcode,

                "custom_unit_price": product.lst_price,

                "product_uom_id": product_uom.uom_id.id,
            })

            obj_order._compute_discount()

            line_id = obj_order.id

        # -------------------------------------------------
        # CREDIT LIMIT
        # -------------------------------------------------

        order._check_credit_limit()

        # -------------------------------------------------
        # RETURN SCAN INFORMATION
        # -------------------------------------------------

        return {
            "success": True,

            "product_id": product.id,

            "name": product.display_name,

            "line_id": line_id,

            "quantity": new_qty,
        }