# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    partner_id = fields.Many2one(comodel_name='res.partner', string='Vendor',required=True)
    floor_id = fields.Many2one(comodel_name='floor.product', string='Floor')
    brand_id = fields.Many2one(comodel_name='brand.brand', string='Brand',required=True)
    color_id = fields.Many2one(comodel_name='color.color', string='Color')
    size_id = fields.Many2one(comodel_name='size.size', string='Size',required=True)
    seasons_id = fields.Many2one(comodel_name='seasons.seasons', string='Seasons',required=True)

    margin_percentage = fields.Float(
        string='Margin %',
    )
    is_in_pricelist = fields.Boolean(
        string="In Pricelist",
        compute='_compute_is_in_pricelist',
        search='_search_is_in_pricelist',
        store=False,
    )
    discount_percent = fields.Float(string='Disc. %', compute='_compute_pricelist_discount')
    discount_amount = fields.Float(string='Disc Amt', compute='_compute_pricelist_discount')

    @api.depends('brand_id', 'color_id', 'size_id')
    def _compute_display_name(self):
        super()._compute_display_name()
        for product in self:
            parts = [product.display_name]
            for field in ('brand_id', 'color_id', 'size_id'):
                value = product[field]
                if value:
                    parts.append(value.name)
            product.display_name = " - ".join(filter(None, parts))

    def _compute_pricelist_discount(self):
        pricelist_id = self.env.context.get('discount_pricelist_id')
        items = {}
        if pricelist_id:
            for item in self.env['product.pricelist.item'].search([
                ('pricelist_id', '=', pricelist_id),
                ('product_tmpl_id', 'in', self.ids),
                ('applied_on', '=', '1_product'),
            ]):
                items.setdefault(item.product_tmpl_id.id, item)  # first matching rule
        for rec in self:
            item = items.get(rec.id)
            rec.discount_percent = item.percent_price if item else 0.0
            rec.discount_amount = item.discount_amount if item else 0.0

    def _pricelist_item_domain(self):
        domain = [('product_tmpl_id', '!=', False)]
        pricelist_id = self.env.context.get('discount_pricelist_id')
        if pricelist_id:
            domain.append(('pricelist_id', '=', pricelist_id))
        return domain

    def _compute_is_in_pricelist(self):
        domain = self._pricelist_item_domain() + [('product_tmpl_id', 'in', self.ids)]
        items = self.env['product.pricelist.item']._read_group(
            domain=domain, groupby=['product_tmpl_id'],
        )
        tmpl_ids_with_rule = {tmpl.id for tmpl, in items}
        for product in self:
            product.is_in_pricelist = product.id in tmpl_ids_with_rule

    def _search_is_in_pricelist(self, operator, value):
        items = self.env['product.pricelist.item']._read_group(
            domain=self._pricelist_item_domain(), groupby=['product_tmpl_id'],
        )
        tmpl_ids_with_rule = [tmpl.id for tmpl, in items]
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', tmpl_ids_with_rule)]
        return [('id', 'not in', tmpl_ids_with_rule)]

    @api.onchange('margin_percentage')
    def _onchange_margin_percentage(self):
        for rec in self:
            if rec.list_price and rec.margin_percentage:
                margin_amount = rec.list_price * (rec.margin_percentage / 100)
                rec.standard_price = rec.list_price - margin_amount


    uom_line_ids = fields.One2many(
        "product.template.uom.line",
        "product_tmpl_id",
        string="Units"
    )

    # def write(self, vals):
    #     res = super().write(vals)
    #     if 'floor_id' in vals:
    #         for template in self:
    #             if len(template.product_variant_ids) == 1:
    #                 template.product_variant_ids.floor_id = template.floor_id.id
    #
    #     return res
    #
    # @api.model_create_multi
    # def create(self, vals_list):
    #     templates = super().create(vals_list)
    #     for template in templates:
    #         if len(template.product_variant_ids) == 1 and template.floor_id:
    #             template.product_variant_ids.floor_id = template.floor_id.id
    #
    #     return templates

    @api.constrains('name', 'brand_id', 'color_id', 'size_id', 'seasons_id', 'partner_id')
    def _check_duplicate_product(self):
        for rec in self:
            if rec.name:
                duplicate = self.env['product.template'].search([
                    ('id', '!=', rec.id),
                    ('name', '=ilike', rec.name),
                    ('brand_id', '=', rec.brand_id.id),
                    ('color_id', '=', rec.color_id.id),
                    ('size_id', '=', rec.size_id.id),
                    ('seasons_id', '=', rec.seasons_id.id),
                    ('partner_id', '=', rec.partner_id.id),
                    ('default_code', '=', rec.default_code),
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        _('A product with same Name, Style Code ,Brand, Color, Size, Season and Partner already exists.')
                    )

    @api.model_create_multi
    def create(self, vals_list):
        default_vendor = self.env['res.partner'].search([], limit=1)

        default_brand = self.env['brand.brand'].search([], limit=1)
        default_size = self.env['size.size'].search([], limit=1)
        default_season = self.env['seasons.seasons'].search([], limit=1)

        for vals in vals_list:

            if not vals.get('partner_id'):
                vals['partner_id'] = default_vendor.id

            if not vals.get('brand_id'):
                vals['brand_id'] = default_brand.id

            if not vals.get('size_id'):
                vals['size_id'] = default_size.id

            if not vals.get('seasons_id'):
                vals['seasons_id'] = default_season.id

            if not vals.get('barcode'):
                vals['barcode'] = self.env['ir.sequence'].next_by_code('bm.sequence')

        return super().create(vals_list)

    @api.model
    def name_search(self, name='', domain=None, operator='ilike', limit=100):
        domain = domain or []

        if name:
            # =========================================
            # NORMAL PRODUCT SEARCH
            # + PRODUCT.UOM BARCODE SEARCH
            # =========================================

            product_uoms = self.env['product.uom'].search([
                ('barcode', 'ilike', name),
            ])

            uom_product_ids = product_uoms.mapped(
                'product_id.product_tmpl_id'
            ).ids

            search_domain = expression.OR([
                # Normal product fields
                [
                    ('name', operator, name),
                ],
                [
                    ('default_code', operator, name),
                ],
                [
                    ('barcode', operator, name),
                ],

                # product.uom barcode
                [
                    ('id', 'in', uom_product_ids),
                ],
            ])

            products = self.search(
                expression.AND([
                    domain,
                    search_domain,
                ]),
                limit=limit
            )

            return [
                (product.id, product.display_name)
                for product in products
            ]

        products = self.search(
            domain,
            limit=limit
        )

        return [
            (product.id, product.display_name)
            for product in products
        ]

class ProductTemplateUomLine(models.Model):
    _name = "product.template.uom.line"
    _description = "Product UOM Line"

    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="cascade"
    )

    uom_id = fields.Many2one(
        "uom.uom",
        string="Unit Name",
        required=True
    )

    product_uom_id = fields.Many2one(
        "product.uom",
        readonly=True,
        ondelete="cascade"
    )
    barcode = fields.Char(
        string='Barcode'
    )

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)

        ProductUom = self.env['product.uom']

        for line in lines:
            product = line.product_tmpl_id.product_variant_id

            puom = ProductUom.create({
                'product_id': product.id,
                'uom_id': line.uom_id.id,
            })

            line.product_uom_id = puom.id
            line.barcode = puom.barcode

        return lines

    @api.constrains('product_tmpl_id', 'uom_id')
    def _check_duplicate_uom(self):
        for rec in self:
            duplicate = self.search([
                ('id', '!=', rec.id),
                ('product_tmpl_id', '=', rec.product_tmpl_id.id),
                ('uom_id', '=', rec.uom_id.id),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    _("This Unit is already added for this product.")
                )

    def unlink(self):
        product_uoms = self.mapped('product_uom_id')

        res = super().unlink()

        if product_uoms:
            product_uoms.unlink()

        return res

    def action_print_barcode(self):
        self.ensure_one()

        if self.product_uom_id:
            return self.env.ref(
                'product.report_product_packaging'
            ).report_action(self.product_uom_id)

    def write(self, vals):
        res = super().write(vals)

        if 'barcode' in vals:
            for line in self:
                if line.product_uom_id:
                    line.product_uom_id.barcode = line.barcode

        return res