# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

class ProductTemplateUomLineInherit(models.Model):
    _inherit = "product.template.uom.line"

    def action_open_print_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Print Barcode',
            'res_model': 'uom.line.print.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_line_ids': [(6, 0, self.ids)]},
        }