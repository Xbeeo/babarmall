# -*- coding: utf-8 -*-

from odoo import fields, models


class Color(models.Model):
    _name = "color.color"
    _description = "Color"

    name = fields.Char(string='Name',required=True)