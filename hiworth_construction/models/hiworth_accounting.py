from openerp import fields, models, api
from openerp.osv import fields as old_fields

import time
from datetime import datetime
import datetime
#from openerp.osv import fields
from openerp import tools
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from pychart.arrow import default
from cookielib import vals_sorted_by_key
# from pygments.lexer import _default_analyse
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP



class account_account(models.Model):
    _inherit = 'account.account'
    
    @api.multi
    @api.depends('name')            
    def _count_no_of_invoices(self):
        for line in self:
#             print 'q=================', self.env['res.partner'].search([('property_account_payable','=', line.id)])
            partner_id = self.env['res.partner'].search([('property_account_payable','=', line.id)])
            
            if len(partner_id) != 0:
                print 'partner========', partner_id[0].id
                invoice_ids = self.env['hiworth.invoice'].search([('partner_id','=',partner_id[0].id)])
                line.invoice_count = len(invoice_ids)
        
    location_id = fields.Many2one('stock.location', 'Plot')
    invoice_count = fields.Float(compute='_count_no_of_invoices',  string="Invoice Count")
    is_contractor_payable = fields.Boolean('Is Contractor Payable')
    is_cash_bank = fields.Boolean('Cash/Bank')
    
class account_move_line(models.Model):
    _inherit = 'account.move.line'
    
    @api.onchange('invoice_no_id2')
    def _onchange_invoice_no(self):
        invoice_ids = []
        invoice_obj = self.env['hiworth.invoice'].search([('state','in',['approve','partial'])])
        invoice_ids = [invoice.id for invoice in invoice_obj]
        if self.invoice_no_id2.id != False:
            self.invoice_no2_balance = self.invoice_no_id2.balance+self.debit
        return {'domain': {'invoice_no_id2': [('id','in',invoice_ids)]}}
        
    location_id = fields.Many2one('stock.location', 'Plot')
    invoice_no_id2 = fields.Many2one('hiworth.invoice', 'Invoice No')
    invoice_no_id3 = fields.Many2one('hiworth.invoice', 'Invoice No')
    invoice_no2_balance = fields.Float('Balance')
    cheque_no = fields.Char('Cheque No')
    
    
    @api.multi
    def open_invice(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['hiworth.invoice'].search([('id','=',self.invoice_no_id2.id)])

        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Invoice Form View',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'hiworth.invoice',
            'view_id':'hiworth_invoice_form',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }
        

    @api.multi
    def open_account(self):
        self.ensure_one()
        treeview_id = self.env.ref('hiworth_accounting.view_account_form_hiworth').id
         
        record =  self.env['account.account'].search([('id','=',self.account_id.id)])
 
        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        return {
            'name': 'Account',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.account',
            'views': [(treeview_id, 'form')],      
            'target': 'current',
            'res_id':res_id,
        }
        
    
#     def _default_get(self, cr, uid, fields, context=None):
#         #default_get should only do the following:
#         #   -propose the next amount in debit/credit in order to balance the move
#         #   -propose the next account from the journal (default debit/credit account) accordingly
#         context = dict(context or {})
#         account_obj = self.pool.get('account.account')
#         period_obj = self.pool.get('account.period')
#         journal_obj = self.pool.get('account.journal')
#         move_obj = self.pool.get('account.move')
#         tax_obj = self.pool.get('account.tax')
#         fiscal_pos_obj = self.pool.get('account.fiscal.position')
#         partner_obj = self.pool.get('res.partner')
#         currency_obj = self.pool.get('res.currency')
# 
#         if not context.get('journal_id', False):
#             context['journal_id'] = context.get('search_default_journal_id', False)
#         if not context.get('period_id', False):
#             context['period_id'] = context.get('search_default_period_id', False)
#         context = self.convert_to_period(cr, uid, context)
# 
#         # Compute simple values
#         data = super(account_move_line, self).default_get(cr, uid, fields, context=context)
#         if context.get('journal_id'):
#             total = 0.0
#             #in account.move form view, it is not possible to compute total debit and credit using
#             #a browse record. So we must use the context to pass the whole one2many field and compute the total
#             if context.get('line_id'):
#                 for move_line_dict in move_obj.resolve_2many_commands(cr, uid, 'line_id', context.get('line_id'), context=context):
#                     data['name'] = data.get('name') or move_line_dict.get('name')
#                     data['partner_id'] = data.get('partner_id') or move_line_dict.get('partner_id')
#                     total += move_line_dict.get('debit', 0.0) - move_line_dict.get('credit', 0.0)
#             elif context.get('period_id'):
#                 #find the date and the ID of the last unbalanced account.move encoded by the current user in that journal and period
#                 move_id = False
#                 cr.execute('''SELECT move_id, date FROM account_move_line
#                     WHERE journal_id = %s AND period_id = %s AND create_uid = %s AND state = %s
#                     ORDER BY id DESC limit 1''', (context['journal_id'], context['period_id'], uid, 'draft'))
#                 res = cr.fetchone()
#                 move_id = res and res[0] or False
#                 data['date'] = res and res[1] or period_obj.browse(cr, uid, context['period_id'], context=context).date_start
#                 data['move_id'] = move_id
#                 if move_id:
#                     #if there exist some unbalanced accounting entries that match the journal and the period,
#                     #we propose to continue the same move by copying the ref, the name, the partner...
#                     move = move_obj.browse(cr, uid, move_id, context=context)
#                     data.setdefault('name', move.line_id[-1].name)
#                     same_partner = len({l.partner_id for l in move.line_id}) == 1
#                     for l in move.line_id:
#                         data['partner_id'] = data.get('partner_id') or (same_partner and l.partner_id.id)
#                         data['ref'] = data.get('ref') or l.ref
#                         total += (l.debit or 0.0) - (l.credit or 0.0)
# 
#             #compute the total of current move
#             data['debit'] = total < 0 and -total or 0.0
#             data['credit'] = total > 0 and total or 0.0
#             #pick the good account on the journal accordingly if the next proposed line will be a debit or a credit
#             journal_data = journal_obj.browse(cr, uid, context['journal_id'], context=context)
#             account = total > 0 and journal_data.default_credit_account_id or journal_data.default_debit_account_id
#             #map the account using the fiscal position of the partner, if needed
#             if isinstance(data.get('partner_id'), (int, long)):
#                 part = partner_obj.browse(cr, uid, data['partner_id'], context=context)
#             elif isinstance(data.get('partner_id'), (tuple, list)):
#                 part = partner_obj.browse(cr, uid, data['partner_id'][0], context=context)
#             else:
#                 part = False
#             if account and part:
#                 account = fiscal_pos_obj.map_account(cr, uid, part and part.property_account_position or False, account.id)
#                 account = account_obj.browse(cr, uid, account, context=context)
#             data['account_id'] =  account and account.id or False
#             #compute the amount in secondary currency of the account, if needed
#             if account and account.currency_id:
#                 data['currency_id'] = account.currency_id.id
#                 #set the context for the multi currency change
#                 compute_ctx = context.copy()
#                 compute_ctx.update({
#                         #the following 2 parameters are used to choose the currency rate, in case where the account
#                         #doesn't work with an outgoing currency rate method 'at date' but 'average'
#                         'res.currency.compute.account': account,
#                         'res.currency.compute.account_invert': True,
#                     })
#                 if data.get('date'):
#                     compute_ctx.update({'date': data['date']})
#                 data['amount_currency'] = currency_obj.compute(cr, uid, account.company_id.currency_id.id, data['currency_id'], -total, context=compute_ctx)
#         data = self._default_get_move_form_hook(cr, uid, data)
#         return data
        
     
        