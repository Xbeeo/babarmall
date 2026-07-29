# -*- coding: utf-8 -*-

from odoo import fields, models


class PartyType(models.Model):
    _name = "party.type"
    _description = "Party Type"

    name = fields.Char(string='Name',required=True)