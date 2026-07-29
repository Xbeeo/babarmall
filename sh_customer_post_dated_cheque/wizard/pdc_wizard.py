# Copyright (C) Softhealer Technologies.

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.http import request
from datetime import timedelta, datetime, date


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    pdc_id = fields.Many2one('pdc.wizard')


class PDC_wizard(models.Model):
    _name = "pdc.wizard"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "PDC Wizard"

    # pdc only be allowed to delete in draft state
    def unlink(self):

        for rec in self:
            if rec.state != 'draft':
                raise UserError("You can only delete draft state pdc")

        return super(PDC_wizard, self).unlink()

    def action_register_check(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')
        active_id = self.env.context.get('active_id')
        account_move_model = self.env[active_model].browse(active_id)

        # if account_move_model.move_type not in ('out_invoice'):
        #     raise UserError("Only Customer invoice are considered!")

        if account_move_model.move_type not in ('out_invoice', 'in_invoice'):
            raise UserError("Only Customer Invoice or Vendor Bill are considered!")

        move_listt = []
        payment_amount = 0.0

        if len(active_ids) > 0:
            account_moves = self.env[active_model].browse(active_ids)
            partners = account_moves.mapped('partner_id')
            if len(set(partners)) != 1:
                raise UserError('Partners must be same')

            states = account_moves.mapped('state')
            if len(set(states)) != 1 or states[0] != 'posted':
                raise UserError(
                    'Only posted invoices are considered for PDC payment!!')

            for account_move in account_moves:
                if account_move.payment_state != 'paid' and account_move.amount_residual != 0.0:
                    payment_amount = payment_amount + account_move.amount_residual
                    move_listt.append(account_move.id)

        if not move_listt:
            raise UserError("Selected invoices are already paid!!")

        return {
            'name': 'PDC Payment',
            'res_model': 'pdc.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('sh_customer_post_dated_cheque.sh_pdc_wizard_form_wizard').id,
            'context': {
                'default_invoice_ids': [(6, 0, move_listt)],
                'default_partner_id': account_move_model.partner_id.id,
                'default_payment_amount': payment_amount,
                'default_payment_type': 'receive_money'
            },
            'target': 'new',
            'type': 'ir.actions.act_window'
        }

    def open_attachments(self):
        [action] = self.env.ref('base.action_attachment').read()

        action['domain'] = [('id', 'in', self.attachment_ids.ids)]
        return action

    def open_journal_items(self):
        [action] = self.env.ref('account.action_account_moves_all').read()
        ids = self.env['account.move.line'].search([('pdc_id', '=', self.id)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    def open_journal_entry(self):
        [action] = self.env.ref(
            'sh_customer_post_dated_cheque.sh_pdc_action_move_journal_line').read()
        ids = self.env['account.move'].search([('pdc_id', '=', self.id)])
        id_list = []
        for pdc_id in ids:
            id_list.append(pdc_id.id)
        action['domain'] = [('id', 'in', id_list)]
        return action

    @api.model
    def default_get(self, fields):
        rec = super(PDC_wizard, self).default_get(fields)
        active_ids = self._context.get('active_ids')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec
        invoices = self.env['account.move'].browse(active_ids)
        if invoices and len(invoices) == 1:
            invoice = invoices[0]
            if invoice.move_type in ('out_invoice', 'out_refund'):
                rec.update({'payment_type': 'receive_money'})

            rec.update({'partner_id': invoice.partner_id.id,
                        'payment_amount': invoice.amount_residual,
                        'invoice_id': invoice.id,
                        'due_date': invoice.invoice_date_due,
                        'memo': invoice.name})

        return rec

    name = fields.Char("Name", default='New', readonly=1, tracking=True)
    payment_type = fields.Selection(
        [('receive_money', 'Receive Money')], string="Payment Type", default='receive_money', tracking=True)
    partner_id = fields.Many2one(
        'res.partner', string="Partner", tracking=True)
    payment_amount = fields.Monetary("Payment Amount", tracking=True)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  default=lambda self: self.env.company.currency_id, tracking=True)
    reference = fields.Char("Cheque Reference", tracking=True)
    journal_id = fields.Many2one('account.journal', string="Payment Journal", domain=[
                                 ('type', '=', 'bank')], required=1, tracking=True)
    cheque_status = fields.Selection([('draft', 'Draft'), ('deposit', 'Deposit'), (
        'paid', 'Paid')], string="Cheque Status", default='draft', tracking=True)
    payment_date = fields.Date(
        "Payment Date", default=fields.Date.today(), required=1, tracking=True)
    due_date = fields.Date("Due Date", required=1, tracking=True)
    memo = fields.Char("Memo", tracking=True)
    agent = fields.Char("Agent", tracking=True)
    pdc_holder = fields.Many2one('res.partner', 'PDC Holder' , tracking=True)
    bank_id = fields.Many2one('res.bank', string="Bank", tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Cheque Image')
    company_id = fields.Many2one(
        'res.company', string='company', default=lambda self: self.env.company, tracking=True)
    invoice_id = fields.Many2one(
        'account.move', string="Invoice/Bill", tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('registered', 'Registered'), ('returned', 'Returned'),
                              ('deposited', 'Deposited'), ('bounced', 'Bounced'), ('done', 'Done'), ('cancel', 'Cancelled')], string="State", default='draft', tracking=True)
    deposited_debit = fields.Many2one('account.move.line')
    deposited_credit = fields.Many2one('account.move.line')

    invoice_ids = fields.Many2many('account.move')
    account_move_ids = fields.Many2many(
        'account.move', compute="compute_account_moves",)
    done_date = fields.Date(string="Done Date", readonly=True, tracking=True)
    # attachment_ids = fields.One2many(
    #    'ir.attachment', 'pdc_id', string="Attachments")

    pdc_type = fields.Selection(
        [
            ('customer', 'Customer'),
            ('vendor', 'Vendor'),
        ],
        string="PDC Type",
        default='customer',
        tracking=True,
        required=True
    )

    @api.onchange('pdc_type')
    def _onchange_pdc_type(self):
        self.partner_id = False

        if self.pdc_type == 'customer':
            return {
                'domain': {
                    'partner_id': [('customer_rank', '>', 0)]
                }
            }

        elif self.pdc_type == 'vendor':
            return {
                'domain': {
                    'partner_id': [('supplier_rank', '>', 0)]
                }
            }

    @api.depends('payment_type', 'partner_id','pdc_type')
    def compute_account_moves(self):

        self.account_move_ids = False
        domain = [('partner_id', '=', self.partner_id.id), ('payment_state', '!=',
                                                            'paid'), ('amount_residual', '!=', 0.0), ('state', '=', 'posted')]

        # if self.payment_type == 'receive_money':
        #     domain.extend([('move_type', '=', 'out_invoice')])

        if self.pdc_type == 'customer':
            domain.append(('move_type', '=', 'out_invoice'))

        elif self.pdc_type == 'vendor':
            domain.append(('move_type', '=', 'in_invoice'))

        moves = self.env['account.move'].search(domain)
        self.account_move_ids = moves.ids

    @api.onchange('partner_id','pdc_type')
    def _onchange_partner(self):

        if self.env.company.auto_fill_open_invoice:

            domain = [('partner_id', '=', self.partner_id.id), ('payment_state', '!=',
                                                                'paid'), ('amount_residual', '!=', 0.0), ('state', '=', 'posted')]

            # if self.payment_type == 'receive_money':
            #     domain.extend([('move_type', '=', 'out_invoice')])

            if self.pdc_type == 'customer':
                domain.append(('move_type', '=', 'out_invoice'))

            elif self.pdc_type == 'vendor':
                domain.append(('move_type', '=', 'in_invoice'))

            moves = self.env['account.move'].search(domain)

            self.invoice_ids = [(6, 0, moves.ids)]

    # Register pdc payment
    def button_register(self):
        listt = []
        if self:
            if self.invoice_id:
                listt.append(self.invoice_id.id)
            if self.invoice_ids:
                listt.extend(self.invoice_ids.ids)

            self.write({
                'invoice_ids': [(6, 0, list(set(listt)))]
            })

            if self.cheque_status == 'draft':
                self.write({'state': 'draft'})

            if self.cheque_status == 'deposit':
                self.action_register()
                self.action_deposited()
                self.write({'state': 'deposited'})

            if self.cheque_status == 'paid':
                self.action_register()
                self.action_deposited()
                self.action_done()
                self.write({'state': 'done'})
#

    def action_register(self):
        self.check_payment_amount()

        if self.invoice_ids:
            list_amount_residuals = self.invoice_ids.mapped('amount_residual')
            amount = (self.currency_id.round(sum(list_amount_residuals))
                      if self.currency_id else round(sum(list_amount_residuals), 2))

            if self.payment_amount > amount and amount != 0:
                raise UserError(
                    "Payment amount is greater than total invoice amount!!!")

        move = self.env['account.move']

        pdc_account = self.check_pdc_account()
        partner_account = self.get_partner_account()

        move_line_vals_debit = {}
        move_line_vals_credit = {}

        # if self.payment_type == 'receive_money':
        #     move_line_vals_debit = self.get_debit_move_line(pdc_account)
        #     move_line_vals_credit = self.get_credit_move_line(partner_account)

        if self.pdc_type == 'customer':

            move_line_vals_debit = self.get_debit_move_line(pdc_account)
            move_line_vals_credit = self.get_credit_move_line(partner_account)


        elif self.pdc_type == 'vendor':

            move_line_vals_debit = self.get_debit_move_line(partner_account)
            move_line_vals_credit = self.get_credit_move_line(pdc_account)

        move_vals = self.get_move_vals(
            move_line_vals_debit,
            move_line_vals_credit
        )

        total_amount_residuals = sum(
            self.invoice_ids.mapped('amount_residual')
        )

        if self.invoice_ids and total_amount_residuals != 0:
            move_id = move.create(move_vals)
            move_id.action_post()

            self.write({
                'deposited_debit': move_id.line_ids.filtered(lambda x: x.debit > 0),
                'deposited_credit': move_id.line_ids.filtered(lambda x: x.credit > 0)
            })

        self.write({'state': 'registered'})

    def check_payment_amount(self):
        if self.payment_amount <= 0.0:
            raise UserError("Amount must be greater than zero!")

    # def check_pdc_account(self):
    #     if self.payment_type == 'receive_money':
    #         if not self.env.company.pdc_customer:
    #             raise UserError(
    #                 "Please Set PDC payment account for Customer !")
    #         else:
    #             return self.env.company.pdc_customer.id

    def check_pdc_account(self):
        if self.pdc_type == 'customer':
            if not self.env.company.pdc_customer:
                raise UserError(
                    "Please Set PDC Customer Account!"
                )
            return self.env.company.pdc_customer.id

        elif self.pdc_type == 'vendor':
            if not self.env.company.pdc_vendor:
                raise UserError(
                    "Please Set PDC Vendor Account!"
                )
            return self.env.company.pdc_vendor.id

    # def get_partner_account(self):
    #     if self.payment_type == 'receive_money':
    #         return self.partner_id.property_account_receivable_id.id

    def get_partner_account(self):
        if self.pdc_type == 'customer':
            return self.partner_id.property_account_receivable_id.id

        elif self.pdc_type == 'vendor':
            return self.partner_id.property_account_payable_id.id

    def action_returned(self):
        self.check_payment_amount()
        self.write({'state': 'returned'})

    def get_credit_move_line(self, account):
        return {
            'pdc_id': self.id,
            # 'partner_id': self.partner_id.id,
            'account_id': account,
            'credit': self.payment_amount,
            'ref': self.memo,
            'date': self.payment_date,
            'date_maturity': self.due_date,
        }

    def get_debit_move_line(self, account):
        return {
            'pdc_id': self.id,
            # 'partner_id': self.partner_id.id,
            'account_id': account,
            'debit': self.payment_amount,
            'ref': self.memo,
            'date': self.payment_date,
            'date_maturity': self.due_date,
        }

    def get_move_vals(self, debit_line, credit_line):
        return {
            'pdc_id': self.id,
            'date': self.payment_date,
            'journal_id': self.journal_id.id,
            # 'partner_id': self.partner_id.id,
            'ref': self.memo,
            'move_type': 'entry',
            'line_ids': [(0, 0, debit_line),
                         (0, 0, credit_line)]
        }

    def action_deposited(self):
        # move = self.env['account.move']
        #
        # self.check_payment_amount()  # amount must be positive
        # pdc_account = self.check_pdc_account()
        # partner_account = self.get_partner_account()
        #
        # # Create Journal Item
        # move_line_vals_debit = {}
        # move_line_vals_credit = {}
        # if self.payment_type == 'receive_money':
        #     move_line_vals_debit = self.get_debit_move_line(pdc_account)
        #     move_line_vals_credit = self.get_credit_move_line(partner_account)
        #
        # # create move and post it
        # move_vals = self.get_move_vals(
        #     move_line_vals_debit, move_line_vals_credit)

        self.write({
            'state': 'deposited',
        })

        # total_amount_residuals = sum(
        #     self.invoice_ids.mapped('amount_residual'))
        # if self.invoice_ids and total_amount_residuals != 0:
        #
        #     move_id = move.create(move_vals)
        #     move_id.action_post()
        #     self.write({'deposited_debit': move_id.line_ids.filtered(lambda x: x.debit > 0),
        #                 'deposited_credit': move_id.line_ids.filtered(lambda x: x.credit > 0)})

    def action_bounced(self):
        move = self.env['account.move']

        self.check_payment_amount()  # amount must be positive
        pdc_account = self.check_pdc_account()
        partner_account = self.get_partner_account()

        # Create Journal Item
        move_line_vals_debit = {}
        move_line_vals_credit = {}

        # if self.payment_type == 'receive_money':
        #     move_line_vals_debit = self.get_debit_move_line(partner_account)
        #     move_line_vals_credit = self.get_credit_move_line(pdc_account)

        if self.pdc_type == 'customer':

            move_line_vals_debit = self.get_debit_move_line(partner_account)
            move_line_vals_credit = self.get_credit_move_line(pdc_account)

        elif self.pdc_type == 'vendor':

            move_line_vals_debit = self.get_debit_move_line(pdc_account)
            move_line_vals_credit = self.get_credit_move_line(partner_account)

        if self.memo:
            move_line_vals_debit.update({'name': 'PDC Payment :'+self.memo})
            move_line_vals_credit.update({'name': 'PDC Payment :'+self.memo})
        else:
            move_line_vals_debit.update({'name': 'PDC Payment'})
            move_line_vals_credit.update({'name': 'PDC Payment'})
        # create move and post it
        move_vals = self.get_move_vals(
            move_line_vals_debit, move_line_vals_credit)

        total_amount_residuals = sum(
            self.invoice_ids.mapped('amount_residual'))
        if self.invoice_ids and total_amount_residuals != 0:
            move_id = move.create(move_vals)
            move_id.action_post()

        self.write({'state': 'bounced'})

    # def action_done(self):
    #     move = self.env['account.move']
    #
    #     self.check_payment_amount()  # amount must be positive
    #     pdc_account = self.check_pdc_account()
    #     # bank_account = self.journal_id.payment_debit_account_id.id or self.journal_id.payment_credit_account_id.id
    #     bank_account = self.journal_id._get_journal_inbound_outstanding_payment_accounts()
    #     bank_account = bank_account[0].id if bank_account else False
    #
    #     # Create Journal Item
    #     move_line_vals_debit = {}
    #     move_line_vals_credit = {}
    #     # if self.payment_type == 'receive_money':
    #     #     move_line_vals_debit = self.get_debit_move_line(bank_account)
    #     #     move_line_vals_credit = self.get_credit_move_line(pdc_account)
    #
    #     if self.pdc_type == 'customer':
    #
    #         move_line_vals_debit = self.get_debit_move_line(bank_account)
    #         move_line_vals_credit = self.get_credit_move_line(pdc_account)
    #
    #
    #     elif self.pdc_type == 'vendor':
    #
    #         move_line_vals_debit = self.get_debit_move_line(pdc_account)
    #         move_line_vals_credit = self.get_credit_move_line(bank_account)
    #
    #     if self.memo:
    #         move_line_vals_debit.update(
    #             {'name': 'PDC Payment :'+self.memo, 'partner_id': self.partner_id.id})
    #         move_line_vals_credit.update(
    #             {'name': 'PDC Payment :'+self.memo, 'partner_id': self.partner_id.id})
    #     else:
    #         move_line_vals_debit.update(
    #             {'name': 'PDC Payment', 'partner_id': self.partner_id.id})
    #         move_line_vals_credit.update(
    #             {'name': 'PDC Payment', 'partner_id': self.partner_id.id})
    #
    #     # create move and post it
    #     move_vals = self.get_move_vals(
    #         move_line_vals_debit, move_line_vals_credit)
    #
    #     # invoice = self.env['account.move'].sudo().search([('name','=',self.memo)])
    #     # if invoice:
    #     total_amount_residuals = sum(
    #         self.invoice_ids.mapped('amount_residual'))
    #     if self.invoice_ids and total_amount_residuals != 0:
    #
    #         move_id = move.create(move_vals)
    #         move_id.action_post()
    #
    #         payment_amount = self.payment_amount
    #         for invoice in self.invoice_ids:
    #
    #             if self.payment_type == 'receive_money':
    #                 # reconcilation Entry for Invoice
    #                 debit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', invoice.id),
    #                                                                              ('debit', '>', 0.0)], limit=1)
    #
    #                 credit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', move_id.id),
    #                                                                               ('credit', '>', 0.0)], limit=1)
    #
    #                 if debit_move_id and credit_move_id and payment_amount > 0:
    #                     # full_reconcile_id = self.env['account.full.reconcile'].sudo().create({
    #                     # })
    #
    #                     if payment_amount > invoice.amount_residual:
    #                         amount = invoice.amount_residual
    #
    #                     else:
    #                         amount = payment_amount
    #
    #                     payment_amount -= invoice.amount_residual
    #
    #                     partial_reconcile_id_1 = self.env['account.partial.reconcile'].sudo().create({'debit_move_id': debit_move_id.id,
    #                                                                                                   'credit_move_id': credit_move_id.id,
    #                                                                                                   'amount': amount,
    #                                                                                                   'debit_amount_currency': amount,
    #                                                                                                   'credit_amount_currency': 0
    #                                                                                                   })
    #
    #                     partial_reconcile_id_2 = self.env['account.partial.reconcile'].sudo().create({'debit_move_id': self.deposited_debit.id,
    #                                                                                                   'credit_move_id': self.deposited_credit.id,
    #                                                                                                   'amount': amount,
    #                                                                                                   'debit_amount_currency': amount,
    #                                                                                                   'credit_amount_currency': 0
    #                                                                                                   })
    #                     if invoice.amount_residual == 0:
    #                         involved_lines = []
    #
    #                         debit_invoice_line_id = self.env['account.move.line'].search(
    #                             [('move_id', '=', invoice.id), ('debit', '>', 0)], limit=1)
    #                         partial_reconcile_ids = self.env['account.partial.reconcile'].sudo().search(
    #                             [('debit_move_id', '=', debit_invoice_line_id.id)])
    #
    #                         for partial_reconcile_id in partial_reconcile_ids:
    #                             involved_lines.append(
    #                                 partial_reconcile_id.credit_move_id.id)
    #                             involved_lines.append(
    #                                 partial_reconcile_id.debit_move_id.id)
    #                         self.env['account.full.reconcile'].create({
    #                             'partial_reconcile_ids': [(6, 0, partial_reconcile_ids.ids)],
    #                             'reconciled_line_ids': [(6, 0, involved_lines)],
    #                         })
    #
    #                     involved_lines = [
    #                         self.deposited_debit.id, self.deposited_credit.id]
    #
    #                     self.env['account.full.reconcile'].create({
    #                         'partial_reconcile_ids': [(6, 0, [partial_reconcile_id_2.id])],
    #                         'reconciled_line_ids': [(6, 0, involved_lines)],
    #                     })
    #
    #             else:
    #                 # reconcilation Entry for Invoice
    #                 credit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', invoice.id),
    #                                                                               ('credit', '>', 0.0)], limit=1)
    #
    #                 debit_move_id = self.env['account.move.line'].sudo().search([('move_id', '=', move_id.id),
    #                                                                              ('debit', '>', 0.0)], limit=1)
    #
    #                 if debit_move_id and credit_move_id and payment_amount > 0:
    #
    #                     if payment_amount > invoice.amount_residual:
    #                         amount = invoice.amount_residual
    #
    #                     else:
    #                         amount = payment_amount
    #
    #                     payment_amount -= invoice.amount_residual
    #
    #                     reconcile_id = self.env['account.partial.reconcile'].sudo().create({'debit_move_id': debit_move_id.id,
    #                                                                                         'credit_move_id': credit_move_id.id,
    #                                                                                         'amount': amount,
    #                                                                                         'credit_amount_currency': amount,
    #                                                                                         'debit_amount_currency': 0
    #                                                                                         })
    #                     reconcile_id = self.env['account.partial.reconcile'].sudo().create({'debit_move_id': self.deposited_debit.id,
    #                                                                                         'credit_move_id': self.deposited_credit.id,
    #                                                                                         'amount': amount,
    #                                                                                         'debit_amount_currency': amount,
    #                                                                                         'credit_amount_currency': 0
    #                                                                                         })
    #
    #     else:
    #         bank_account = self.journal_id._get_journal_inbound_outstanding_payment_accounts()
    #         bank_account = bank_account[0].id if bank_account else False
    #         partner_account = self.get_partner_account()
    #
    #         debit_move_line = {
    #             'pdc_id': self.id,
    #             'partner_id': self.partner_id.id,
    #             'account_id': bank_account,
    #             'debit': self.payment_amount,
    #             'ref': self.memo,
    #             'date': self.due_date,
    #             'date_maturity': self.due_date,
    #         }
    #
    #         credit_move_line = {
    #             'pdc_id': self.id,
    #             'partner_id': self.partner_id.id,
    #             'account_id': partner_account,
    #             'credit': self.payment_amount,
    #             'ref': self.memo,
    #             'date': self.due_date,
    #             'date_maturity': self.due_date,
    #         }
    #
    #         move_vals = {
    #             'pdc_id': self.id,
    #             'date': self.due_date,
    #             'journal_id': self.journal_id.id,
    #             'ref': self.memo,
    #             'line_ids': [(0, 0, debit_move_line),
    #                          (0, 0, credit_move_line)]
    #         }
    #
    #         move = self.env['account.move'].create(move_vals)
    #         move.action_post()
    #
    #     self.write({
    #         'state': 'done',
    #         'done_date': date.today(),
    #     })

    def action_done(self):
        move = self.env['account.move']

        self.check_payment_amount()

        pdc_account = self.check_pdc_account()

        bank_account = self.journal_id._get_journal_inbound_outstanding_payment_accounts()
        bank_account = bank_account[0].id if bank_account else False

        move_line_vals_debit = {}
        move_line_vals_credit = {}

        # Customer PDC
        # Dr Bank
        # Cr PDC Account
        if self.pdc_type == 'customer':

            move_line_vals_debit = self.get_debit_move_line(bank_account)
            move_line_vals_credit = self.get_credit_move_line(pdc_account)


        # Vendor PDC
        # Dr PDC Account
        # Cr Bank
        elif self.pdc_type == 'vendor':

            move_line_vals_debit = self.get_debit_move_line(pdc_account)
            move_line_vals_credit = self.get_credit_move_line(bank_account)

        if self.memo:
            name = 'PDC Payment : ' + self.memo
        else:
            name = 'PDC Payment'

        move_line_vals_debit.update({
            'name': name,
            'partner_id': self.partner_id.id
        })

        move_line_vals_credit.update({
            'name': name,
            'partner_id': self.partner_id.id
        })

        move_vals = self.get_move_vals(
            move_line_vals_debit,
            move_line_vals_credit
        )

        total_amount_residuals = sum(
            self.invoice_ids.mapped('amount_residual')
        )

        if self.invoice_ids and total_amount_residuals != 0:

            move_id = move.create(move_vals)
            move_id.action_post()

            payment_amount = self.payment_amount

            for invoice in self.invoice_ids:

                # ===========================
                # CUSTOMER INVOICE
                # ===========================
                if self.pdc_type == 'customer':

                    invoice_line = self.env['account.move.line'].sudo().search([
                        ('move_id', '=', invoice.id),
                        ('debit', '>', 0)
                    ], limit=1)

                    payment_line = self.env['account.move.line'].sudo().search([
                        ('move_id', '=', move_id.id),
                        ('credit', '>', 0)
                    ], limit=1)



                # ===========================
                # VENDOR BILL
                # ===========================
                else:

                    invoice_line = self.env['account.move.line'].sudo().search([
                        ('move_id', '=', invoice.id),
                        ('credit', '>', 0)
                    ], limit=1)

                    payment_line = self.env['account.move.line'].sudo().search([
                        ('move_id', '=', move_id.id),
                        ('debit', '>', 0)
                    ], limit=1)

                if invoice_line and payment_line and payment_amount > 0:

                    if payment_amount > invoice.amount_residual:
                        amount = invoice.amount_residual
                    else:
                        amount = payment_amount

                    payment_amount -= amount

                    self.env['account.partial.reconcile'].sudo().create({

                        'debit_move_id': invoice_line.id if invoice_line.debit else payment_line.id,

                        'credit_move_id': payment_line.id if payment_line.credit else invoice_line.id,

                        'amount': amount,

                        'debit_amount_currency': amount,

                        'credit_amount_currency': amount,

                    })


        else:

            # No invoice selected case

            partner_account = self.get_partner_account()

            if self.pdc_type == 'customer':

                debit_account = bank_account
                credit_account = partner_account


            else:

                debit_account = partner_account
                credit_account = bank_account

            move_vals = {

                'pdc_id': self.id,
                'date': self.due_date,
                'journal_id': self.journal_id.id,
                'ref': self.memo,

                'line_ids': [

                    (0, 0, {
                        'pdc_id': self.id,
                        'partner_id': self.partner_id.id,
                        'account_id': debit_account,
                        'debit': self.payment_amount,
                        'date': self.due_date,
                        'date_maturity': self.due_date,
                    }),

                    (0, 0, {
                        'pdc_id': self.id,
                        'partner_id': self.partner_id.id,
                        'account_id': credit_account,
                        'credit': self.payment_amount,
                        'date': self.due_date,
                        'date_maturity': self.due_date,
                    })

                ]
            }

            move_id = self.env['account.move'].create(move_vals)
            move_id.action_post()

        self.write({
            'state': 'done',
            'done_date': date.today()
        })

    # form view cancel button
    def action_cancel(self):
        self.action_delete_related_moves()
        if self.company_id.pdc_operation_type == 'cancel':
            self.write({'state': 'cancel'})

        elif self.company_id.pdc_operation_type == 'cancel_draft':
            self.write({'state': 'draft'})

        elif self.company_id.pdc_operation_type == 'cancel_delete':
            self.write({'state': 'draft'})
            self.unlink()

    # multi action methods
    def action_pdc_cancel(self):
        self.action_delete_related_moves()
        self.write({'state': 'cancel'})

    def action_pdc_cancel_draft(self):
        self.action_delete_related_moves()
        self.write({'state': 'draft'})

    def action_pdc_cancel_delete(self):
        self.action_delete_related_moves()
        self.write({'state': 'draft'})
        self.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('payment_type') == 'receive_money':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pdc.payment.customer')

            res = super(PDC_wizard, self).create(vals)
            res.attachment_ids.write({
                'res_id': res.id
            })

        return res

    # ==============================
    #    CRON SCHEDULER CUSTOMER
    # ==============================

    @api.model
    def notify_customer_due_date(self):
        emails = []
        if self.env.company.is_cust_due_notify:
            notify_day_1 = self.env.company.notify_on_1
            notify_day_2 = self.env.company.notify_on_2
            notify_day_3 = self.env.company.notify_on_3
            notify_day_4 = self.env.company.notify_on_4
            notify_day_5 = self.env.company.notify_on_5
            notify_date_1 = False
            notify_date_2 = False
            notify_date_3 = False
            notify_date_4 = False
            notify_date_5 = False
            if notify_day_1:
                notify_date_1 = fields.date.today() + timedelta(days=int(notify_day_1)*-1)
            if notify_day_2:
                notify_date_2 = fields.date.today() + timedelta(days=int(notify_day_2)*-1)
            if notify_day_3:
                notify_date_3 = fields.date.today() + timedelta(days=int(notify_day_3)*-1)
            if notify_day_4:
                notify_date_4 = fields.date.today() + timedelta(days=int(notify_day_4)*-1)
            if notify_day_5:
                notify_date_5 = fields.date.today() + timedelta(days=int(notify_day_5)*-1)

            records = self.search([('payment_type', '=', 'receive_money')])
            for user in self.env.company.sh_user_ids:
                if user.partner_id and user.partner_id.email:
                    emails.append(user.partner_id.email)
            email_values = {
                'email_to': ','.join(emails),
            }
            view = self.env.ref(
                "sh_customer_post_dated_cheque.sh_pdc_payment_form_view", raise_if_not_found=False).sudo()
            view_id = view.id if view else 0
            for record in records:
                if (record.due_date == notify_date_1
                    or record.due_date == notify_date_2
                    or record.due_date == notify_date_3
                    or record.due_date == notify_date_4
                        or record.due_date == notify_date_5):

                    if self.env.company.is_notify_to_customer:
                        # template_download_id = record.env['ir.model.data'].get_object(
                        #     'sh_customer_post_dated_cheque', 'sh_pdc_company_to_customer_notification_1'
                        #     )
                        template_download_id = self.env.ref(
                            'sh_customer_post_dated_cheque.sh_pdc_company_to_customer_notification_1')
                        _ = record.env['mail.template'].browse(
                            template_download_id.id
                        ).send_mail(record.id, email_layout_xmlid='mail.mail_notification_light', force_send=True)
                    if self.env.company.is_notify_to_user and self.env.company.sh_user_ids:
                        url = ''
                        base_url = request.env['ir.config_parameter'].sudo(
                        ).get_param('web.base.url')
                        url = base_url + "/web#id=" + \
                            str(record.id) + \
                            "&&model=pdc.wizard&view_type=form&view_id=" + \
                            str(view_id)
                        ctx = {
                            "customer_url": url,
                        }
                        # template_download_id = record.env['ir.model.data'].get_object(
                        #     'sh_customer_post_dated_cheque', 'sh_pdc_company_to_int_user_notification_1'
                        #     )
                        template_download_id = self.env.ref(
                            'sh_customer_post_dated_cheque.sh_pdc_company_to_int_user_notification_1')
                        _ = request.env['mail.template'].sudo().browse(template_download_id.id).with_context(ctx).send_mail(
                            record.id, email_values=email_values, email_layout_xmlid='mail.mail_notification_light', force_send=True)

    # Multi Action Starts for change the state of PDC check
    def action_set_draft(self):
        self.sudo().write({
            'state': 'draft',
        })

    def action_delete_related_moves(self):

        for model in self:
            move_ids = self.env['account.move'].search(
                [('pdc_id', '=', model.id)])
            for move in move_ids:
                move.button_draft()
                lines = self.env['account.move.line'].search(
                    [('move_id', '=', move.id)])
                lines.unlink()

            model.sudo().write({
                'done_date': False
            })

            for move in move_ids:
                self.env.cr.execute(
                    """ delete from account_move where id =%s""" % (move.id,))

    def action_state_register(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'draft':
                    for active_model in active_models:
                        active_model.action_register()
                else:
                    raise UserError(
                        "Only Draft state PDC check can switch to Register state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_return(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'registered':
                    for active_model in active_models:
                        active_model.action_returned()
                else:
                    raise UserError(
                        "Only Register state PDC check can switch to return state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_deposit(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] in ['registered', 'returned', 'bounced']:
                    for active_model in active_models:
                        active_model.action_deposited()
                else:
                    raise UserError(
                        "Only Register,Return and Bounce state PDC check can switch to Deposit state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_bounce(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'deposited':
                    for active_model in active_models:
                        active_model.action_bounced()
                else:
                    raise UserError(
                        "Only Deposit state PDC check can switch to Bounce state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_done(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] == 'deposited':
                    for active_model in active_models:
                        active_model.action_done()
                else:
                    raise UserError(
                        "Only Deposit state PDC check can switch to Done state!!")
            else:
                raise UserError(
                    "States must be same!!")

    def action_state_cancel(self):
        active_ids = self.env.context.get('active_ids')
        active_model = self.env.context.get('active_model')

        if len(active_ids) > 0:
            active_models = self.env[active_model].browse(active_ids)
            states = active_models.mapped('state')

            if len(set(states)) == 1:
                if states[0] in ['registered', 'returned', 'bounced']:
                    for active_model in active_models:
                        active_model.action_cancel()
                else:
                    raise UserError(
                        "Only Register,Return and Bounce state PDC check can switch to Cancel state!!")
            else:
                raise UserError(
                    "States must be same!!")
