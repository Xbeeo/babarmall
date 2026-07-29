# Copyright (C) Softhealer Technologies.

from . import models
from . import wizard


# def post_init_hook(env):
#     for company in env['res.company'].sudo().search([]):
#         company.write({
#             'pdc_customer': env['account.account'].search([('name', '=', 'PDC Receivable'), ('company_ids', 'in', company.id)], limit=1).id
#         })
