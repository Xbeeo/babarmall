from odoo import api, fields, models
from odoo.exceptions import UserError


class BadDebtReportWizard(models.TransientModel):
    _name = 'bad.debt.report.wizard'
    _description = 'Bad Debt Report Wizard'

    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')

    def action_print(self):
        self.ensure_one()
        if self.date_from > self.date_to:
            raise UserError("Date From cannot be after Date To.")
        return self.env.ref('xbo_abm_report.action_report_bad_debt').report_action(self)