# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'


    allowed_location_id = fields.Many2many(
        comodel_name='stock.location',
        string='Allowed Location',
        help='Allowed Location for this user'
    )

    floor_id = fields.Many2one(comodel_name='floor.product', string='Floor')

    def write(self, values):
        res = super().write(values)
        fields_to_check = ['allowed_location_id']

        if self.ids and any(field in values for field in fields_to_check):
            self.env.registry.clear_cache()
        return res