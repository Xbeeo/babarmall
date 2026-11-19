# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class UomLinePrintWizard(models.TransientModel):
    _name = "uom.line.print.wizard"
    _description = "Print Barcode Wizard"

    qty = fields.Integer(string="Print Qty", default=1, required=True)
    line_ids = fields.Many2many(
        "product.template.uom.line",
        string="Selected Products",
    )

    def action_print(self):
        self.ensure_one()

        if self.qty < 1:
            raise ValidationError(_("Print Quantity must be at least 1."))

        doc_ids = []

        for line in self.line_ids:
            if not line.product_uom_id:
                continue

            qty = line.print_qty if line.print_qty > 0 else self.qty

            doc_ids += [line.product_uom_id.id] * qty

        if not doc_ids:
            raise UserError(_("No valid lines found to print."))

        return self.env.ref(
            'product.report_product_packaging'
        ).report_action(doc_ids)