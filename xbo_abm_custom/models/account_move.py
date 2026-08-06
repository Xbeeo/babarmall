# -*- coding: utf-8 -*-

from odoo import fields, models,api

class AccountMove(models.Model):
    _inherit = 'account.move'

    partner_current_balance = fields.Monetary(string="Current Balance", compute='_compute_partner_current_balance')
    ref_by_id = fields.Many2one(comodel_name='res.partner', string="Ref. By", readonly=True)
    ref_by = fields.Char(string="Ref. By", readonly=True)
    product_catg_id = fields.Many2one(comodel_name='product.category', string="Product Category")
    no_of_bags = fields.Integer(string="No of Bags", readonly=True)
    no_of_ctn = fields.Integer(string="No of CTN", readonly=True)
    party_type_id = fields.Many2one(
        comodel_name='party.type',
        string="Party Type",
        readonly=True
    )
    salesmen_id = fields.Many2one(comodel_name='hr.employee', string="Salesmen")
    checker_id = fields.Many2one(comodel_name='hr.employee', string="Checker")
    packer_id = fields.Many2one(comodel_name='hr.employee', string="Packer")

    show_confirm_button = fields.Boolean(
        compute="_compute_show_confirm_button"
    )

    @api.depends('party_type_id')
    def _compute_show_confirm_button(self):
        for rec in self:
            if rec.party_type_id.name == 'Credit':
                rec.show_confirm_button = rec.env.user.has_group(
                    'xbo_abm_custom.group_show_confirm_button_invoice'
                )
            else:
                rec.show_confirm_button = True

    total_before_dis = fields.Float(
        string="Total Before Discount",
        compute="_compute_total_before_dic",
        store=True,
    )
    total_discount = fields.Float(
        string="Total Discount",
        compute="_compute_total_discount",
        store=True,
    )

    @api.depends('invoice_line_ids.discount_amount')
    def _compute_total_discount(self):
        for move in self:
            total = 0.0
            for line in move.invoice_line_ids:
                total += line.discount_amount
            move.total_discount = total

    @api.depends('invoice_line_ids.quantity', 'invoice_line_ids.price_unit')
    def _compute_total_before_dic(self):
        for move in self:
            total = 0.0
            for line in move.invoice_line_ids:
                total += line.quantity * line.price_unit
            move.total_before_dis = total

    customer_credit_limit = fields.Integer(string="Credit limit",readonly=True)
    start_date_time = fields.Datetime(string="Start Date Time", readonly=True)
    end_date_time = fields.Datetime(string="End Date Time", readonly=True)
    sale_person_id = fields.Many2one(comodel_name='res.users', string="User", readonly=True)
    custom_stock_pick_id  = fields.Many2one(comodel_name='stock.picking', string="Stock Picking")

    """COMPUTE PARTNER CURRENT BALANCE"""

    @api.depends('partner_current_balance', 'partner_id')
    def _compute_partner_current_balance(self):
        for rec in self:
            if rec.partner_id and rec.move_type in ['in_invoice','out_invoice']:
                rec.partner_current_balance = rec.partner_id.credit - rec.partner_id.debit
            else:
                rec.partner_current_balance = False
