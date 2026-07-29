# -*- coding: utf-8 -*-

from odoo import fields, models


class ProductVariantInherit(models.Model):
    _inherit = 'product.product'

    partner_id = fields.Many2one(comodel_name='res.partner', string='Vendor',related='product_tmpl_id.partner_id', store=True)
    floor_id = fields.Many2one(comodel_name='floor.product', string='Floor',related='product_tmpl_id.floor_id', store=True)
    brand_id = fields.Many2one(comodel_name='brand.brand', string='Brand',related='product_tmpl_id.brand_id', store=True)
    color_id = fields.Many2one(comodel_name='color.color', string='Color',related='product_tmpl_id.color_id', store=True)
    size_id =  fields.Many2one(comodel_name='size.size', string='Size',related='product_tmpl_id.size_id', store=True)
    seasons_id = fields.Many2one(comodel_name='seasons.seasons',related='product_tmpl_id.seasons_id', store=True)
    margin_percentage = fields.Float(
        string='Margin %',related='product_tmpl_id.margin_percentage', store=True
    )
