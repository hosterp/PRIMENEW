from openerp.exceptions import except_orm, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, api, _
from openerp import workflow
import time
import datetime
from datetime import date
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import timedelta
from pychart.arrow import default
from openerp.osv import osv, expression


class partner_statement_line(models.Model):
    _name = 'partner.statement.line'

    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None: 
            context = {}
        line_num = 1    
        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context) 
            line_num = 1
            for line_rec in first_line_rec.statement_id.statement_ids: 
                line_rec.line_no = line_num 
                line_num += 1
            line_num = 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    name = fields.Char('Name')
    date = fields.Date('Date')
    amount = fields.Float('Amount')
#     credit = fields.Float('Credit')
    total = fields.Float('Total')
    statement_id = fields.Many2one('partner.statement', 'Statement')
    
    
    
class partner_statement(models.Model):
    _name = 'partner.statement'
    
    @api.multi
    @api.depends('statement_ids')
    def _compute_total(self):
        for line in self:
            line.total =0.0
            for lines in line.statement_ids:
                line.total += lines.amount
    
    name = fields.Char('Name')
    partner_id = fields.Many2one('res.partner', 'Partner')
    account_id = fields.Many2one('account.account', 'Related Account')
    statement_ids = fields.One2many('partner.statement.line', 'statement_id', 'Statement Lines')
    total = fields.Float(compute='_compute_total', string="Total Amount")
#     move_lines = fields.One2many(related='account_id.move_lines',  string='Payments',)
    
    @api.model
    def create(self,vals):
#         print 'self============================',vals['project_id']
        if vals['account_id']:
            self_obj = self.env['partner.statement']
            line = self_obj.search([('account_id','=',vals['account_id'])])
            print 'qqqqqqqqqqqqqqqqqqq', line,len(line) 
            if len(line) != 0:
                raise osv.except_osv(_('Warning'),_("The related account already selected for a Statement Entry. Please select other account"))
        return super(partner_statement, self).create(vals) 
    
    
# class account_move_line(models.Model):
#     _inherit = "account.move.line"
#      
#     statement_id = fields.Many2one('partner.statement', 'Partner Statement')
    
    
    