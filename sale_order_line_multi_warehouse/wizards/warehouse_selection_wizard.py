# -*- coding: utf-8 -*-

from odoo import fields, models,api

class WarehouseSelectionWizard(models.TransientModel):
    _name = 'warehouse.selection.wizard'

    product_id = fields.Many2one('product.product')
    partner_id = fields.Many2one('res.partner')
    move_type = fields.Selection([
        ('out_invoice', 'Customer Invoice'),
        ('in_invoice', 'Vendor Bill'),
        ('internal', 'Internal'),

    ])

    line_ids = fields.One2many(
        'warehouse.selection.wizard.line',
        'wizard_id'
    )
    invoice_line_ids = fields.One2many(
        'warehouse.selection.wizard.invoice',
        'wizard_id',
        string="Invoices"
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)

        product_obj = self.env['product.product'].browse(
            self.env.context.get('default_product_id')
        )

        partner_obj = self.env['res.partner'].browse(
            self.env.context.get('default_partner_id')
        )

        move_type = self.env.context.get('default_move_type')
        res['product_id'] = product_obj.id
        res['partner_id'] = partner_obj.id
        res['move_type'] = move_type

        lines = []

        quants = self.env['stock.quant'].read_group(
            [
                ('product_id', '=', product_obj.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal'),
            ],
            ['location_id', 'quantity:sum'],
            ['location_id'],
        )

        for quant in quants:
            lines.append((0, 0, {
                'location_id': quant['location_id'][0],
                'qty_available': quant['quantity'],
            }))

        res['line_ids'] = lines

        invoice_lines = []
        if move_type != 'internal':
            invoice_move_lines = self.env['account.move.line'].search([
                ('product_id', '=', product_obj.id),
                ('move_id.partner_id', '=', partner_obj.id),
                ('move_id.move_type', '=', move_type),
                ('move_id.state', '=', 'posted'),
            ])

            for line in invoice_move_lines:
                invoice_lines.append((0, 0, {
                    'move_id': line.move_id.id,
                    'partner_id': line.move_id.partner_id.id,
                    'invoice_date': line.move_id.invoice_date,
                    'product_id': line.product_id.id,
                    'quantity': line.quantity,
                    'price_unit': line.price_unit,
                    'tax_ids': [(6, 0, line.tax_ids.ids)],
                    'price_subtotal': line.price_subtotal,
                    'price_total': line.price_total,
                    'currency_id': line.currency_id.id,
                }))

            res['invoice_line_ids'] = invoice_lines

        return res

    # def action_apply(self):
    #     locations = self.line_ids.filtered(
    #         lambda x: x.selected
    #     ).mapped('location_id')
    #
    #     self.sale_line_id.write({
    #         'warehouse_location_ids': [(6, 0, locations.ids)]
    #     })
    #
    #     return {'type': 'ir.actions.act_window_close'}


class WarehouseSelectionWizardLine(models.TransientModel):
    _name = 'warehouse.selection.wizard.line'

    wizard_id = fields.Many2one(
        'warehouse.selection.wizard'
    )

    location_id = fields.Many2one(
        'stock.location',
        string="Warehouse"
    )

    qty_available = fields.Float(
        string="Quantity On Hand"
    )

    selected = fields.Boolean(
        string="Add Warehouse"
    )

class WarehouseSelectionWizardInvoice(models.TransientModel):
    _name = 'warehouse.selection.wizard.invoice'

    wizard_id = fields.Many2one('warehouse.selection.wizard')

    move_id = fields.Many2one(
        'account.move',
        string="Invoice"
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Customer"
    )

    invoice_date = fields.Date(
        string="Invoice Date"
    )

    product_id = fields.Many2one(
        'product.product',
        string="Product"
    )

    quantity = fields.Float(
        string="Quantity"
    )

    price_unit = fields.Float(
        string="Price"
    )

    tax_ids = fields.Many2many(
        'account.tax',
        string="Tax"
    )

    price_subtotal = fields.Monetary(
        string="Tax Excl."
    )

    price_total = fields.Monetary(
        string="Tax Incl."
    )

    currency_id = fields.Many2one(
        'res.currency'
    )