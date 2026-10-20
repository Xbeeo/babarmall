from odoo import models, fields
from odoo.tools.sql import SQL


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    discount_amount = fields.Float(string='Disc Amount', readonly=True)
    discount = fields.Float(string='Discount (%)', readonly=True, aggregator='avg')

    def _select(self) -> SQL:
        return SQL(
            "%s, sum(l.discount_amount) AS discount_amount, avg(l.discount) AS discount",
            super()._select(),
        )