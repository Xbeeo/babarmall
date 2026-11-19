from odoo import api, fields, models
from odoo.exceptions import UserError


class ReportBadDebt(models.AbstractModel):
    _name = 'report.xbo_abm_report.report_bad_debt'
    _description = 'Bad Debt Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        wiz = self.env['bad.debt.report.wizard'].browse(docids)
        domain = [('date', '>=', wiz.date_from), ('date', '<=', wiz.date_to)]
        if wiz.partner_id:
            domain.append(('partner_id', '=', wiz.partner_id.id))
        records = self.env['bad.debt'].search(domain, order='date, id')
        if not records:
            raise UserError("No bad debt records found for the selected criteria.")
        groups = []
        for partner in records.mapped('partner_id'):
            recs = records.filtered(lambda r: r.partner_id == partner)
            balance = partner.credit - partner.debit  # fresh, at print time
            total = sum(recs.mapped('amount'))
            groups.append({
                'partner': partner,
                'balance': balance,
                'records': recs,
                'total': total,
                'net': balance - total,
            })
        return {
            'doc_ids': docids,
            'doc_model': 'bad.debt.report.wizard',
            'docs': wiz,
            'groups': groups,
            'company': self.env.company,
            'printed_on': fields.Datetime.context_timestamp(self, fields.Datetime.now()),
            'printed_by': self.env.user.name,
        }