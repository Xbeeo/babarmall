# -*- coding: utf-8 -*-
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError



class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    partner_current_balance = fields.Monetary(string="Current Balance", compute='_compute_partner_current_balance')
    ref_by_id = fields.Many2one(comodel_name='res.partner', string="Ref. By")
    ref_by = fields.Char(string="Ref. By")
    product_catg_id = fields.Many2one(comodel_name='product.category', string="Product Category")
    total_discount = fields.Float(
        string="Total Discount",
        compute="_compute_total_discount",
        store=True,
    )
    type_of_packing = fields.Selection([('shoping_bag','Shopping Bag'),('ctn','CTN')], string="Type of Packing")
    no_of_bags = fields.Integer(string="No of Bags")
    no_of_ctn = fields.Integer(string="No of CTN")
    start_date_time = fields.Datetime(string="Start Date Time",default=fields.Datetime.now,readonly=True)
    end_date_time = fields.Datetime(string="End Date Time",readonly=True)
    partner_phone = fields.Char(string="Customer Phone",related='partner_id.phone',store=True,readonly=True)
    customer_credit_limit = fields.Integer(string="Credit limit",related='partner_id.customer_credit_limit',store=True,readonly=True)
    party_type_id = fields.Many2one(
        comodel_name='party.type',
        string="Party Type",
        related='partner_id.party_type_id',
        store=True,
        readonly=True
    )

    salesmen_id = fields.Many2one(comodel_name='hr.employee', string="Salesmen")
    checker_id = fields.Many2one(comodel_name='hr.employee', string="Checker")
    packer_id =  fields.Many2one(comodel_name='hr.employee', string="Packer")


    total_before_dis = fields.Float(
        string="Total Before Discount",
        compute="_compute_total_before_dic",
        store=True,
    )



    @api.depends('order_line.product_uom_qty', 'order_line.price_unit')
    def _compute_total_before_dic(self):
        for move in self:
            total = 0.0
            for line in move.order_line:
                total += line.product_uom_qty * line.price_unit
            move.total_before_dis = total

    @api.depends('order_line.discount_amount')
    def _compute_total_discount(self):
        for move in self:
            total = 0.0
            for line in move.order_line:
                total += line.discount_amount
            move.total_discount = total


    """COMPUTE PARTNER CURRENT BALANCE"""

    @api.depends('partner_id')
    def _compute_partner_current_balance(self):
        for rec in self:
            if rec.partner_id:
                rec.partner_current_balance = rec.partner_id.credit - rec.partner_id.debit
            else:
                rec.partner_current_balance = False

    def _check_credit_limit(self):
        for order in self:
            partner = order.partner_id

            if not partner or not partner.customer_credit_limit:
                continue

            # Current partner balance
            current_balance = partner.credit - partner.debit

            # Pending Sale Orders (Invoice not created)
            pending_orders = self.env['sale.order'].search([
                ('partner_id', '=', partner.id),
                ('id', '!=', order.id),
            ])

            pending_amount = 0.0

            for so in pending_orders:
                # Agar koi posted invoice hai to is SO ko skip kar do
                posted_invoice = so.invoice_ids.filtered(
                    lambda inv: inv.state == 'posted' and inv.move_type == 'out_invoice'
                )

                if posted_invoice:
                    continue

                pending_amount += so.amount_total

            # Total Exposure
            exposure = current_balance + pending_amount + order.amount_total

            if exposure > partner.customer_credit_limit:
                raise ValidationError(_("Transaction Total %s Exceeds the Credit Limit >> %s") % (exposure,partner.customer_credit_limit))




    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        orders._check_credit_limit()
        return orders

    def write(self, vals):
        res = super().write(vals)
        self._check_credit_limit()
        return res


    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderInherit, self)._prepare_invoice()
        invoice_vals['ref_by'] = self.ref_by
        invoice_vals['sale_person_id'] = self.user_id.id
        invoice_vals['no_of_bags'] = self.no_of_bags
        invoice_vals['no_of_ctn'] = self.no_of_ctn
        invoice_vals['party_type_id'] = self.party_type_id.id
        invoice_vals['start_date_time'] = self.start_date_time
        invoice_vals['end_date_time'] = self.end_date_time
        return invoice_vals

    def action_confirm(self):
        res = super().action_confirm()

        for order in self:
            order.end_date_time = fields.Datetime.now()

        return res
