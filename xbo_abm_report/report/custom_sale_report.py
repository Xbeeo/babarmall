from odoo import models, fields

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        result = super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
        report = self._get_report(report_ref)
        if res_ids and report.report_name == 'xbo_abm_report.custom_sale_order_report_template':
            for rec in self.env[report.model].browse(res_ids).sudo():
                rec.print_count += 1
        return result