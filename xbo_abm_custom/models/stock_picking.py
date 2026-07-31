# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'
    _description = 'stock.picking.inherit'

    ref_by_id = fields.Many2one(comodel_name='res.partner', string="Ref. By")
    no_of_bags = fields.Integer(string="No of Bags")
    no_of_ctn = fields.Integer(string="No of CTN")

    credit_total = fields.Integer(string="Credit Total", compute='_credit_total')

    """COUNT ALL RELATED Credit Note"""

    def _credit_total(self):
        for rec in self:
            credit_count = self.env['account.move'].search_count(
                [('custom_stock_pick_id', '=', self.id), ('move_type', 'in', ['in_refund','out_refund'])])
            rec.credit_total = credit_count

    """VIEW RELATED Credit Note"""

    def action_view_credit_note(self):
        self.ensure_one()
        result = {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "name": _("Credit Note"),
            'view_mode': 'list,form',
            'domain': [('custom_stock_pick_id', '=', self.id), ('move_type', 'in', ['in_refund','out_refund'])],
        }
        return result

    picking_code = fields.Char(
        compute='_compute_picking_code',
        store=True,
    )

    @api.depends('picking_type_id', 'picking_type_id.code')
    def _compute_picking_code(self):
        for rec in self:
            rec.picking_code = rec.picking_type_id.code or ''

    @api.model_create_multi
    def create(self, vals_list):
        pickings = super().create(vals_list)
        for picking in pickings:
            if picking.origin:
                sale_order = self.env['sale.order'].search(
                    [('name', '=', picking.origin)],
                    limit=1
                )

                if sale_order:
                    picking.ref_by_id = sale_order.ref_by_id.id if sale_order.ref_by_id else None
                    picking.no_of_bags = sale_order.no_of_bags if sale_order.no_of_bags else None
                    picking.no_of_ctn = sale_order.no_of_ctn if sale_order.no_of_ctn else None

        return pickings


    def action_credit_notes(self):
        self.ensure_one()

        invoice_lines = []

        for move in self.move_ids:
            invoice_lines.append((0, 0, {
                "product_id": move.product_id.id,
                "quantity": move.quantity,
            }))

        if self.picking_type_code == 'incoming':
            move_type = 'out_refund'
            name = "Customer Credit Note"

            # Delivery
        elif self.picking_type_code == 'outgoing':
            move_type = 'in_refund'
            name = "Vendor Credit Note"

        else:
            move_type = 'out_refund'
            name = "Credit Note"

        return {
            "type": "ir.actions.act_window",
            "name": name,
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_move_type": move_type,
                "default_partner_id": self.partner_id.id,
                "default_company_id": self.company_id.id,
                'default_custom_stock_pick_id': self.id,
                "default_invoice_line_ids": invoice_lines,
            },
        }


