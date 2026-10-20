from odoo import api, fields, models

class ResPartnerInherit(models.Model):
    _inherit = "res.partner"

    pdc_count = fields.Integer(compute='_compute_pdc_count')

    def _compute_pdc_count(self):
        data = self.env['pdc.wizard']._read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'], ['__count'])
        counts = {partner.id: count for partner, count in data}
        for partner in self:
            partner.pdc_count = counts.get(partner.id, 0)

    def action_view_pdc_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'PDC Payments',
            'res_model': 'pdc.wizard',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }