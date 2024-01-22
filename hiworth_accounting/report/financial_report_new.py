from openerp import models, fields, api, _
from datetime import datetime, date, time


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    account_type = fields.Selection(related='account_id.user_type.report_type', string="Account Type", store=True)
    journal_type = fields.Selection(related='move_id.journal_id.type', string="Journal Type", store=True)
    status = fields.Selection(related='move_id.state', store=True, string="Status", copy=False)

class FinancialHiworthReportWizard(models.TransientModel):
    _name = "hiworth.financial.report.wizard"


    date_from = fields.Date('Start period',required=True)
    date_to = fields.Date('End period',required=True)
    company_id = fields.Many2one('res.company', string='Chart of Account',required=True)
    target_move = fields.Selection([
                ('posted', 'All Posted Entries'),
                ('all', 'All Entries')
                ],default='posted',string='Target Moves',required=True)
    fiscalyear = fields.Many2one('account.fiscalyear', 'Fiscal year', help='Keep empty for all open fiscal year')
    account_report_id = fields.Selection([
                ('balance_sheet', 'Balance Sheet'),
                ('profit_loss', 'Profit and Loss')
                ],string='Account Reports',required=True)
    visible_details = fields.Boolean('WIth Details', default=False)
    cloud = fields.Boolean('Cloud', default=False)

    _defaults = {
            'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.common.report',context=c)
        }

    @api.onchange('company_id')
    def onchange_dates(self):
      var = date.today().strftime('%Y-%m-%d')
      records = self.env['account.fiscalyear'].search([('company_id','=',self.company_id.id),('date_start','<=',var),('date_stop','>=',var)])
      for record_id in records:
        self.fiscalyear = record_id.id
        self.date_from = record_id.date_start
        self.date_to = var



    @api.multi
    def action_open_window1(self):


       datas = {
           'ids': self._ids,
           'model': self._name,
           'form': self.read(),
           'context':self._context,
       }

       return{
           'name' : 'Balance sheet Report',
           'type' : 'ir.actions.report.xml',
           'report_name' : 'hiworth_accounting.report_hiworth_financial_template',
           'datas': datas,
           'report_type': 'qweb-pdf'
       }

    @api.multi
    def action_view_window(self):


       datas = {
           'ids': self._ids,
           'model': self._name,
           'form': self.read(),
           'context':self._context,
       }

       return{
           'name' : 'Balance sheet Report',
           'type' : 'ir.actions.report.xml',
           'report_name' : 'hiworth_accounting.report_hiworth_financial_template',
           'datas': datas,
           'report_type': 'qweb-html'
       }


    @api.multi
    def get_asset_lines(self):
        move_ids = []
        parent_ids = []
        account_ids = []
        dict = {'parent':"", 'amount':0, 'account_list':[{'account':"",'amount':0}]}
        list = []
        list.append(dict)
        account_obj = self.env['account.account']
        if self.cloud == False:
          if self.target_move == 'posted':
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','=','asset'),'|',('cloud','=',False),('cloud','=','no')])
          else:
              orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','=','asset'),'|',('cloud','=',False),('cloud','=','no')])
        if self.cloud == True:
          if self.target_move == 'posted':
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','=','asset'),'|',('cloud','=',False),('cloud','=','yes')])
          else:
              orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','=','asset'),'|',('cloud','=',False),('cloud','=','yes')])
        for order in orders:
            final_list = filter(lambda x: x['parent'] == order.account_id.parent_id.name, list)
            if len(final_list) == 0:
                list.append({'parent':order.account_id.parent_id.name, 'amount':order.debit-order.credit, 'account_list':[{'account':order.account_id.name,'amount':order.debit-order.credit}]})
            if len(final_list) != 0:
                a = list.index(final_list[0])
                list[a]['amount'] += order.debit
                list[a]['amount'] -= order.credit
                if self.visible_details == True:
                    final_list1 = filter(lambda x: x['account'] == order.account_id.name, list[a]['account_list'])
                    if len(final_list1) == 0:
                        list[a]['account_list'].append({'account':order.account_id.name,'amount':order.debit-order.credit})
                    if len(final_list1) != 0:
                        b = list[a]['account_list'].index(final_list1[0])
                        list[a]['account_list'][b]['amount'] += order.debit
                        list[a]['account_list'][b]['amount'] -= order.credit
        return list


    @api.multi
    def get_liability1_lines(self):
        move_ids = []
        parent_ids = []
        account_ids = []
        dict = {'parent':"", 'amount':0, 'account_list':[{'account':"",'amount':0}]}
        list = []
        list.append(dict)
        account_obj = self.env['account.account']
        if self.cloud == False:
          if self.target_move == 'posted':
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','=','liability'),'|',('cloud','=',False),('cloud','=','no')])
          else:
              orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','=','liability'),'|',('cloud','=',False),('cloud','=','no')])
        if self.cloud == True:
          if self.target_move == 'posted':
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','=','liability'),'|',('cloud','=',False),('cloud','=','yes')])
          else:
              orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','=','liability'),'|',('cloud','=',False),('cloud','=','yes')])
        for order in orders:
            final_list = filter(lambda x: x['parent'] == order.account_id.parent_id.name, list)
            if len(final_list) == 0:
                list.append({'parent':order.account_id.parent_id.name, 'amount':order.credit-order.debit, 'account_list':[{'account':order.account_id.name,'amount':order.credit-order.debit}]})
            if len(final_list) != 0:
                a = list.index(final_list[0])
                list[a]['amount'] -= order.debit
                list[a]['amount'] += order.credit
                if self.visible_details == True:
                    final_list1 = filter(lambda x: x['account'] == order.account_id.name, list[a]['account_list'])
                    if len(final_list1) == 0:
                        list[a]['account_list'].append({'account':order.account_id.name,'amount':order.credit-order.debit})
                    if len(final_list1) != 0:
                        b = list[a]['account_list'].index(final_list1[0])
                        list[a]['account_list'][b]['amount'] -= order.debit
                        list[a]['account_list'][b]['amount'] += order.credit
        return list



    @api.multi
    def get_opening_balance(self):
        list =[]
        if self.cloud == False:
          if self.target_move == 'posted':
              moves = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('journal_type','=','situation'),'|',('cloud','=',False),('cloud','=','no')])
          else:
              moves = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('journal_type','=','situation'),'|',('cloud','=',False),('cloud','=','no')])
        if self.cloud == True:
          if self.target_move == 'posted':
              moves = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('journal_type','=','situation'),'|',('cloud','=',False),('cloud','=','yes')])
          else:
              moves = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('journal_type','=','situation'),'|',('cloud','=',False),('cloud','=','yes')])
        bal = 0
        for move in moves:
          bal += move.debit
          bal -= move.credit
        return bal

    @api.multi
    def get_income_lines(self):
        move_ids = []
        parent_ids = []
        account_ids = []
        dict = {'parent':"", 'amount':0, 'account_list':[{'account':"",'amount':0}]}
        list = []
        list.append(dict)
        account_obj = self.env['account.account']
        if self.cloud == False:
          if self.target_move == 'posted' and self.cloud == False:
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','=','income'),'|',('cloud','=',False),('cloud','=','no')])
          else:
              orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','=','income'),'|',('cloud','=',False),('cloud','=','no')])
        if self.cloud == True:
          if self.target_move == 'posted' and self.cloud == False:
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','=','income'),'|',('cloud','=',False),('cloud','=','yes')])
          else:
              orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','=','income'),'|',('cloud','=',False),('cloud','=','yes')])
        for order in orders:
            print 'order=================', order.cloud
            final_list = filter(lambda x: x['parent'] == order.account_id.parent_id.name, list)
            if len(final_list) == 0:
                list.append({'parent':order.account_id.parent_id.name, 'amount':order.credit-order.debit, 'account_list':[{'account':order.account_id.name,'amount':order.credit-order.debit}]})
            if len(final_list) != 0:
                a = list.index(final_list[0])
                list[a]['amount'] -= order.debit
                list[a]['amount'] += order.credit
                if self.visible_details == True:
                    final_list1 = filter(lambda x: x['account'] == order.account_id.name, list[a]['account_list'])
                    if len(final_list1) == 0:
                        list[a]['account_list'].append({'account':order.account_id.name,'amount':order.credit-order.debit})
                    if len(final_list1) != 0:
                        b = list[a]['account_list'].index(final_list1[0])
                        list[a]['account_list'][b]['amount'] -= order.debit
                        list[a]['account_list'][b]['amount'] += order.credit
        return list



    @api.multi
    def get_expense_lines(self):
        move_ids = []
        parent_ids = []
        account_ids = []
        dict = {'parent':"", 'amount':0, 'account_list':[{'account':"",'amount':0}]}
        list = []
        list.append(dict)
        account_obj = self.env['account.account']
        if self.cloud == False:
          if self.target_move == 'posted':
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','=','expense'),'|',('cloud','=',False),('cloud','=','no')])
          else:
              orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','=','expense'),'|',('cloud','=',False),('cloud','=','no')])
        if self.cloud == True:
          if self.target_move == 'posted':
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','=','expense'),'|',('cloud','=',False),('cloud','=','yes')])
          else:
              orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','=','expense'),'|',('cloud','=',False),('cloud','=','yes')])
        for order in orders:
            final_list = filter(lambda x: x['parent'] == order.account_id.parent_id.name, list)
            if len(final_list) == 0:
                list.append({'parent':order.account_id.parent_id.name, 'amount':order.debit-order.credit, 'account_list':[{'account':order.account_id.name,'amount':order.debit-order.credit}]})
            if len(final_list) != 0:
                a = list.index(final_list[0])
                list[a]['amount'] += order.debit
                list[a]['amount'] -= order.credit
                if self.visible_details == True:
                    final_list1 = filter(lambda x: x['account'] == order.account_id.name, list[a]['account_list'])
                    if len(final_list1) == 0:
                        list[a]['account_list'].append({'account':order.account_id.name,'amount':order.debit-order.credit})
                    if len(final_list1) != 0:
                        b = list[a]['account_list'].index(final_list1[0])
                        list[a]['account_list'][b]['amount'] += order.debit
                        list[a]['account_list'][b]['amount'] -= order.credit
        return list



    @api.multi
    def get_profit_loss(self):
      expense_amt = income_amt = i_debit = i_credit = e_debit = e_credit = profit_loss = 0
      if self.cloud == False:
        if self.target_move == 'posted':
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','in',['income','expense']),'|',('cloud','=',False),('cloud','=','no')])
        else:
          orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','in',['income','expense']),'|',('cloud','=',False),('cloud','=','no')])
      if self.cloud == True:
        if self.target_move == 'posted':
            orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('status','=','posted'),('account_type','in',['income','expense']),'|',('cloud','=',False),('cloud','=','yes')])
        else:
          orders = self.env['account.move.line'].search([('date','>=',self.date_from),('date','<=',self.date_to),('company_id','=',self.company_id.id),('account_type','in',['income','expense']),'|',('cloud','=',False),('cloud','=','yes')])
      for order in orders:
        if order.account_id.user_type.report_type == 'expense':
          if order.debit:
            e_debit += order.debit
          if order.credit:
            e_credit += order.credit
        elif order.account_id.user_type.report_type == 'income':
          if order.debit:
            i_debit += order.debit
          if order.credit:
            i_credit += order.credit
      expense_amt = e_debit - e_credit
      income_amt = i_credit - i_debit
      profit_loss = income_amt - expense_amt
      return profit_loss
