# -*- coding: utf-8 -*-

from odoo import fields, models


class CityCity(models.Model):
    _name = "city.city"
    _description = "City City"

    name = fields.Char(string='Name',required=True)