from collections import Counter
from odoo import api, models, _

class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    @api.onchange('item_ids')
    def _onchange_item_ids_explode_multi_products(self):
        commands_to_add = []
        lines_to_remove = []

        for line in self.item_ids:
            tmpls = line.product_tmpl_ids
            if len(tmpls) > 1:
                base_vals = {
                    'applied_on': '1_product',
                    'compute_price': line.compute_price,
                    'fixed_price': line.fixed_price,
                    'percent_price': line.percent_price,
                    'base': line.base,
                    'base_pricelist_id': line.base_pricelist_id.id,
                    'price_discount': line.price_discount,
                    'price_round': line.price_round,
                    'price_surcharge': line.price_surcharge,
                    'price_min_margin': line.price_min_margin,
                    'price_max_margin': line.price_max_margin,
                    'min_quantity': line.min_quantity,
                    'date_start': line.date_start,
                    'date_end': line.date_end,
                }
                for tmpl in tmpls:
                    commands_to_add.append((0, 0, dict(base_vals, product_tmpl_id=tmpl.id)))
                lines_to_remove.append(line)

        if commands_to_add:
            remove_commands = [(3, line.id) for line in lines_to_remove]
            self.item_ids = remove_commands + commands_to_add