from odoo import models


class ReportPartnerLedger(models.AbstractModel):
    _inherit = 'report.accounting_pdf_reports.report_partnerledger'

    def _lines(self, data, partner):
        lines = super()._lines(data, partner)
        created = {l.id: l.create_date for l in
                   self.env['account.move.line'].browse([r['id'] for r in lines])}
        lines.sort(key=lambda r: (r['date'], created[r['id']], r['id']))
        balance = 0.0
        for r in lines:
            balance += r['debit'] - r['credit']
            r['progress'] = balance
        return lines