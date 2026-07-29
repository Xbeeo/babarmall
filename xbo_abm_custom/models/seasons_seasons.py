# -*- coding: utf-8 -*-

from odoo import fields, models


class Seasons(models.Model):
    _name = "seasons.seasons"
    _description = "Seasons"

    name = fields.Char(string='Name',required=True)