# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class BarcodeController(http.Controller):

    @http.route(
        "/barcode_order_scan/add",
        type="json",
        auth="user"
    )
    def add_barcode_product(self, model, order_id, barcode):

        # if model == "sale.order":
        #     return request.env[model].add_product_by_barcode(
        #         order_id,
        #         barcode
        #     )
        #
        # if model == "purchase.order":
        #     return request.env[model].add_product_by_barcode(
        #         order_id,
        #         barcode
        #     )
        #
        # return False

        if model not in (
                "sale.order",
                "purchase.order",
                "stock.picking",
        ):
            return False

        return request.env[model].add_product_by_barcode(
            order_id,
            barcode
        )