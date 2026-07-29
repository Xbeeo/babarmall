# -*- coding: utf-8 -*-

from odoo import fields, models


class FloorProduct(models.Model):
    _name = "floor.product"
    _description = "Floor Product"

    name = fields.Char(string='Name',required=True)