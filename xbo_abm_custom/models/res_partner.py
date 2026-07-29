# -*- coding: utf-8 -*-

from odoo import models , api ,fields, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    customer_credit_limit = fields.Integer(string="Credit limit")
    city_id = fields.Many2one(comodel_name='city.city', string="City")
    party_type_id = fields.Many2one(comodel_name='party.type', string="Party Type",required=True)
    sequence_customer = fields.Char(string="Customer Sequence",default=lambda self: _('New Customer'),readonly=True,copy=False)
    sequence_vendor = fields.Char(string="Vendor Sequence",default=lambda self: _('New Vendor'), readonly=True,copy=False)
    product_ids = fields.One2many(comodel_name='product.product', inverse_name='partner_id',string="Products")

    is_credit = fields.Boolean(compute="_compute_is_credit")

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

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        domain = domain or []

        if name:
            search_domain = expression.OR([
                [('name', operator, name)],
                [('phone', operator, name)],
            ])

            partners = self.search(
                expression.AND([domain, search_domain]),
                limit=limit
            )

            return [
                (
                    partner.id,
                    f"{partner.name} - {partner.phone or ''}"
                )
                for partner in partners
            ]

        return super().name_search(name, domain, operator, limit)