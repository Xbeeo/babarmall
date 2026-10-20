# -*- coding: utf-8 -*-

from odoo import models , api ,fields, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    customer_credit_limit = fields.Integer(string="Credit limit" , tracking=True)
    city_id = fields.Many2one(comodel_name='city.city', string="City" , tracking=True)
    party_type_id = fields.Many2one(comodel_name='party.type', string="Party Type",required=True, tracking=True)
    sequence_customer = fields.Char(string="Customer Sequence",default=lambda self: _('New Customer'),readonly=True,copy=False)
    sequence_vendor = fields.Char(string="Vendor Sequence",default=lambda self: _('New Vendor'), readonly=True,copy=False)
    product_ids = fields.One2many(comodel_name='product.product', inverse_name='partner_id',string="Products")



    is_credit = fields.Boolean(compute="_compute_is_credit")
    customer_current_balance = fields.Monetary(
        string="Current Balance", compute='_compute_current_balance')
    difference = fields.Monetary(
        string="Difference", compute='_compute_current_balance')
    payment_count = fields.Integer(compute='_compute_payment_count')

    def _compute_payment_count(self):
        data = self.env['account.payment']._read_group(
            [('partner_id', 'in', self.ids), ('partner_type', '=', 'customer')],
            ['partner_id'], ['__count'])
        counts = {partner.id: count for partner, count in data}
        for partner in self:
            partner.payment_count = counts.get(partner.id, 0)

    def action_view_customer_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id), ('partner_type', '=', 'customer')],
            'context': {'default_partner_id': self.id, 'default_partner_type': 'customer'},
        }

    @api.depends('credit', 'debit', 'customer_credit_limit')
    def _compute_current_balance(self):
        for partner in self:
            balance = partner.credit - partner.debit
            partner.customer_current_balance = balance
            partner.difference = partner.customer_credit_limit - balance

    @api.depends("party_type_id")
    def _compute_is_credit(self):
        for rec in self:
            if rec.party_type_id and rec.party_type_id.name != "Credit":
                rec.customer_credit_limit = 0
            rec.is_credit = rec.party_type_id.name == "Credit"

    @api.constrains('party_type_id', 'customer_credit_limit')
    def _check_customer_credit_limit(self):
        for rec in self:
            if rec.party_type_id and rec.party_type_id.name == "Credit":
                if rec.customer_credit_limit <= 0:
                    raise ValidationError(
                        _("Credit Limit must be greater than 0.")
                    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)

        for partner in records:
            if partner.customer_rank > 0 and partner.sequence_customer in [False, _('New Customer')]:
                partner.sequence_customer = self.env['ir.sequence'].next_by_code(
                    'customer.sequence'
                )

            if partner.supplier_rank > 0 and partner.sequence_vendor in [False, _('New Vendor')]:
                partner.sequence_vendor = self.env['ir.sequence'].next_by_code(
                    'vendor.sequence'
                )

        return records

    @api.depends(
        "sequence_customer",
        "sequence_vendor",
        "name",
        "phone",
        "street",
        "street2",
        "city_id",
    )
    def _compute_display_name(self):
        for partner in self:
            parts = []

            if partner.sequence_customer and partner.sequence_customer != "New Customer":
                parts.append(partner.sequence_customer)

            if partner.sequence_vendor and partner.sequence_vendor != "New Vendor":
                parts.append(partner.sequence_vendor)

            if partner.name:
                parts.append(partner.name)

            if partner.phone:
                parts.append(partner.phone)

            if partner.street:
                parts.append(partner.street)

            if partner.street2:
                parts.append(partner.street2)

            if partner.city_id:
                parts.append(partner.city_id.name)

            partner.display_name = " - ".join(parts)

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        domain = domain or []

        if name:
            search_domain = expression.OR([
                [
                    ('sequence_customer', operator, name),
                    ('sequence_customer', 'not in', ['New Customer']),
                ],
                [
                    ('sequence_vendor', operator, name),
                    ('sequence_vendor', 'not in', ['New Vendor']),
                ],
                [('name', operator, name)],
                [('phone', operator, name)],
                [('street', operator, name)],
                [('street2', operator, name)],
                [('city_id.name', operator, name)],
            ])

            partners = self.search(
                expression.AND([domain, search_domain]),
                limit=limit
            )

            return [
                (partner.id, partner.display_name)
                for partner in partners
            ]

        partners = self.search(domain, limit=limit)

        return [
            (partner.id, partner.display_name)
            for partner in partners
        ]