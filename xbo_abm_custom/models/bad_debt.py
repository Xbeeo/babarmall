from odoo import api, fields, models


class BadDebt(models.Model):
    _name = 'bad.debt'
    _description = 'Bad Debt'
    _order = 'date desc, id desc'

    date = fields.Date(required=True, default=fields.Date.context_today)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    amount = fields.Float(required=True)
    description = fields.Text(required=True)
    partner_current_balance = fields.Float(
        string='Current Balance',
        compute='_compute_partner_current_balance',
        readonly=True,
    )

    @api.depends('partner_id')
    def _compute_partner_current_balance(self):
        for rec in self:
            if rec.partner_id:
                rec.partner_current_balance = rec.partner_id.credit - rec.partner_id.debit
            else:
                rec.partner_current_balance = False