# -*- coding: utf-8 -*-

from odoo import fields, models


class Size(models.Model):
    _name = "size.size"
    _description = "Size"

    name = fields.Char(string='Name',required=True)