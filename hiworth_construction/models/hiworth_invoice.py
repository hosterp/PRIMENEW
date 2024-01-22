import itertools
import math
from lxml import etree

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from openerp.osv import fields as old_fields, osv, expression
from pychart.arrow import default
from datetime import datetime
import datetime

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund',
}

class hiworth_invoice(models.Model):
    _name = 'hiworth.invoice'
    _order = 'write_date desc'
    
    READONLY_STATES = {
        'approve': [('readonly', True)],
        'partial': [('readonly', True)],
        'paid': [('readonly', True)],
        'cancel': [('readonly', True)]
    }
    
    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency or journal.company_id.currency_id
        
    @api.model
    def _default_journal(self):
        inv_type = self._context.get('type', 'out_invoice')
        inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', filter(None, map(TYPE2JOURNAL.get, inv_types))),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)
#         
#     @api.one
#     @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
#     def _compute_amount(self):
#         self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
#         self.amount_tax = sum(line.amount for line in self.tax_line)
#         self.amount_total = self.amount_untaxed + self.amount_tax  
#         
    @api.onchange('project_id')
    def _onchange_task_selection(self):
        if self.project_id.id != False:
            return {
                'domain': {
                    'task_id': [('project_id','=',self.project_id.id)]
                }                
            }
        
            
    @api.multi
    @api.depends('invoice_line')
    def _compute_invoiced_amount(self):
        for line in self:
            line.invoiced_amount = 0
            for lines in line.invoice_line:
                line.invoiced_amount += lines.price_subtotal
                
    @api.multi
    @api.depends('account_move_lines')
    def _compute_paid_amount(self):
        for line in self:
            line.paid_amount = 0
            for lines in line.account_move_lines:
                line.paid_amount += lines.debit
                
                
    @api.multi
    @api.depends('account_move_lines')
    def _compute_reduction_amount(self):
        for line in self:
            line.reduction_amount = 0
            for lines in line.account_move_lines:
                line.reduction_amount += lines.credit
                
    @api.multi
    @api.depends('grand_total','reduction_amount')
    def _compute_amount_tobe_paid(self):
        for line in self:
            line.amount_to_be_paid = 0
            line.amount_to_be_paid = line.grand_total-line.reduction_amount
                    
    @api.multi
    @api.depends('paid_amount','amount_to_be_paid')
    def _compute_balance(self):
        for line in self:
            line.balance = line.amount_to_be_paid - line.paid_amount
                
    @api.onchange('work_order_id')
    def onchange_work_order(self):
        if self.work_order_id:
            self.project_id = self.work_order_id.project_id.id
            self.partner_id = self.work_order_id.partner_id.id
            self.customer_id = self.work_order_id.project_id.partner_id.id
    @api.multi
    @api.depends('invoiced_amount','discount')       
    def _compute_diccount_amount(self):
        for line in self:
            line.diccount_amount = line.invoiced_amount*(line.discount/100)
    
    @api.multi
    @api.depends('invoiced_amount','diccount_amount')       
    def _compute_total_amount(self):
        for line in self:
            line.total_amount = line.invoiced_amount-line.diccount_amount
     
    @api.multi       
    @api.depends('retention','total_amount')       
    def _compute_retention_amount(self):
        for line in self:
            line.retention_amount = line.total_amount*(line.retention/100)  
            
    @api.multi     
    @api.depends('retention_amount','total_amount')       
    def _compute_net_amount(self):
        for line in self:
            line.net_total = line.total_amount-line.retention_amount
            
    @api.multi
    @api.depends('net_total','addition')       
    def _compute_addition_amount(self):
        for line in self:
            line.addition_amount = line.net_total*(line.addition/100) 
    @api.multi
    @api.depends('net_total','addition_amount','invoice_lines2')       
    def _compute_grand_total_amount(self):
        for line in self:
            if line.is_purchase_bill == True:
                line.grand_total = 0.0
                for lines in line.invoice_lines2:
                    line.grand_total += lines.price_subtotal 
            if line.is_purchase_bill == False: 
                line.grand_total = line.net_total+line.addition_amount
                     
            
    name = fields.Char(string='Reference/Description', index=True,
       states=READONLY_STATES)
    date_invoice = fields.Date('Date')
    partner_id = fields.Many2one('res.partner', string='Partner', change_default=True,
        required=True, states=READONLY_STATES,
        track_visibility='always')
#         readonly=True, states={'draft': [('readonly', False)]},
    origin = fields.Char(string='Source Document',
        help="Reference of the document that produced this invoice.",
        readonly=True, states={'draft': [('readonly', False)]})
    reference = fields.Char(string='Invoice Reference', states=READONLY_STATES,
        help="The partner reference of this invoice.")
    comment = fields.Text('Additional Information', states=READONLY_STATES)
    state = fields.Selection(copy=False, selection=[
            ('draft','Draft'),
            ('waiting','Waiting Approval'),
            ('approve','Approved'),
            ('partial','Partially Paid'),
            ('paid','Paid'),
            ('cancel','Rejected'),
        ], string='Status',  readonly=True, default='draft')
#         compute='_compute_state__get', 
    invoice_line = fields.One2many('hiworth.invoice.line', 'invoice_id', string='Invoice Lines', copy=True,states=READONLY_STATES)
#     readonly=True, states={'draft': [('readonly', False)]},
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('hiworth.invoice'))
    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange',
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user)
    project_id = fields.Many2one('project.project', 'Project', states=READONLY_STATES)
#     task_id = fields.Many2one('project.task', 'Task')
#     agreed_amount = fields.Float(related='task_id.estimated_cost', string="Agreement Amount")
    invoiced_amount = fields.Float(compute='_compute_invoiced_amount', string='Invoiced Amount', states=READONLY_STATES)
    customer_id = fields.Many2one('res.partner', string='Client', states=READONLY_STATES)
    work_order_id = fields.Many2one('work.order', 'Work Order No', states=READONLY_STATES)
    generated_lines = fields.Boolean('Generated Invoice Lines', default=False, states=READONLY_STATES)
    discount =  fields.Float('Discount %',states=READONLY_STATES)
    diccount_amount = fields.Float(compute='_compute_diccount_amount', string='Dicount Amount')
    total_amount = fields.Float(compute='_compute_total_amount', string='Total Bill Amount')
    retention = fields.Float('Retention %',states=READONLY_STATES)
    retention_amount = fields.Float(compute='_compute_retention_amount', string='Retention Amount')
    net_total = fields.Float(compute='_compute_net_amount', string='Net Amount')
    addition = fields.Float('Additions %',states=READONLY_STATES)
    addition_amount = fields.Float(compute='_compute_addition_amount', string='Additions Amount')
    grand_total = fields.Float(compute='_compute_grand_total_amount', string='Grand Amount')
    

    balance = fields.Float(compute='_compute_balance', string="Balance", states=READONLY_STATES)
    reduction_amount = fields.Float(compute='_compute_reduction_amount', string='Paid Amount', states=READONLY_STATES)
    amount_to_be_paid = fields.Float(compute='_compute_amount_tobe_paid', string='Amount To Pay', states=READONLY_STATES)
    paid_amount = fields.Float(compute='_compute_paid_amount', string='Paid Amount', states=READONLY_STATES)
    
    is_purchase_bill = fields.Boolean('Purchase Bill', default=False)
    invoice_lines2 = fields.One2many('hiworth.invoice.line2','invoice_id','Invoice Lines', states=READONLY_STATES)
    purchase_order_date = fields.Datetime('Purchase Order Date', states=READONLY_STATES)
    account_move_lines = fields.One2many('account.move.line', 'invoice_no_id2', 'Payments', states={'paid':[('readonly',True)]})
    account_id = fields.Many2one('account.account', related='partner_id.property_account_payable',  string="Account") 

    
    _defaults = {
        'date_invoice': fields.Date.today(),
        }


    @api.multi
    def open_purchase_order(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['purchase.order'].search([('name','=',self.origin)])

        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Purchase Order view',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'purchase.order',
            'view_id':'purchase_order_form_changed',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }
                
    @api.multi
    def generate_invoice_lines(self):
        self.ensure_one()
        if len(self.invoice_line) > 0:
            raise osv.except_osv(_('Warning!'),
                            _('Some invoice lines are already there. If you want to generate the all lines in work order, First delete the present lines.'))
        order_lines = self.env['work.order.line'].search([('work_order_id','=',self.work_order_id.id)])
        for line in order_lines:
#             invoice_lines = [] 
#             invoice_lines = self.env['hiworth.invoice.line'].search([('work_order_id','=',self.work_order_id.id),('product_id','=',line.product_id.id),('state','!=','cancel')])
#             pre_qty = 0.0
#             for invoice_line in invoice_lines:
#                 pre_qty += invoice_line.quantity
            values = {'product_id': line.product_id.id,
                      'name':line.product_id.name,
                      'total_assigned_qty':line.qty,
                      'uod_id':line.uom_id.id,
                      'price_unit':line.rate,
                      'pre_amount':line.paid_amount,
                      'pre_qty':line.paid_amount/line.rate,
                      'invoice_id':self.id
                      }
            invoice_line_id = self.env['hiworth.invoice.line'].create(values)
            self.generated_lines = True
            
    @api.multi
    def action_for_approval(self):
        for line in self:
            line.state = 'waiting'
             
    @api.multi
    def action_approve(self):
        for line in self:
            line.state = 'approve'
            
    @api.multi
    def action_paid_partial(self):
        for line in self:
            line.state = 'partial'
            if self.origin != False:
                purchase_order =  self.env['purchase.order'].search([('name','=',self.origin)])
                purchase_order.state = 'done'
            for invoice_line in line.invoice_line:
                invoice_line.state = 'partial'
            
             
    @api.multi
    def action_paid(self):
        for line in self:
            for inv in line.invoice_line:
                if (inv.stage_id.approximated_amnt - inv.stage_id.amount_paid) < inv.price_subtotal:
                    raise osv.except_osv(_('Warning!'),
                            _('Amount To Pay is higher'))
                else:
                    inv.stage_id.amount_paid += inv.price_subtotal 
            line.state = 'paid'
            if self.origin != False:
                purchase_order =  self.env['purchase.order'].search([('name','=',self.origin)])
                purchase_order.state = 'paid'
            for invoice_line in line.invoice_line:
                invoice_line.state = 'paid'


    @api.multi
    def action_cancel(self):
        for line in self:
            line.state = 'cancel'
            for invoice_line in line.invoice_line:
                invoice_line.state = 'cancel'
                
    @api.multi
    def set_to_draft(self):
        for line in self:
            line.state = 'draft'
            for invoice_line in line.invoice_line:
                invoice_line.state = 'draft'

    @api.model
    def create(self,vals):
        if 'is_purchase_bill' not in vals:
            now = datetime.datetime.now()
            cb_no = self.env['ir.sequence'].get('cb_no')
    #         print 'teay===================', now.year,nos
            vals['name'] = "INV/CB/TECH/" + str(cb_no)+"/" + str(now.year)
        if 'name' in vals:
            if len(self.env['hiworth.invoice'].search([('name','=',vals['name'])])) > 0:
                raise osv.except_osv(_('Warning!'),
                            _('There is already present an invoice with the same Invoice No.'))
        return super(hiworth_invoice, self).create(vals)
        
    @api.multi
    def write(self,vals):
        if 'name' in vals:
            if len(self.env['hiworth.invoice'].search([('name','=',vals['name'])])) > 1:
                raise osv.except_osv(_('Warning!'),
                            _('There is already present an invoice with the same Invoice No.'))
        super(hiworth_invoice, self).write(vals)
        return True
  
        
        
class hiworth_invoice_line(models.Model):
    _name = 'hiworth.invoice.line'
    _order = "sequence, id"
    
    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
        'product_id')
    def _compute_price(self):
        for line in self:
            line.price_subtotal = line.price_unit*line.quantity
    
    @api.model
    def _default_price_unit(self):
        if not self._context.get('check_total'):
            return 0
        total = self._context['check_total']
        for l in self._context.get('invoice_line', []):
            if isinstance(l, (list, tuple)) and len(l) >= 3 and l[2]:
                vals = l[2]
                price = vals.get('price_unit', 0) * (1 - vals.get('discount', 0) / 100.0)
                total = total - (price * vals.get('quantity'))
                taxes = vals.get('invoice_line_tax_id')
                if taxes and len(taxes[0]) >= 3 and taxes[0][2]:
                    taxes = self.env['account.tax'].browse(taxes[0][2])
                    tax_res = taxes.compute_all(price, vals.get('quantity'),
                        product=vals.get('product_id'), partner=self._context.get('partner_id'))
                    for tax in tax_res['taxes']:
                        total = total - tax['amount']
        return total
        
    @api.multi
    @api.depends('pre_qty', 'quantity')
    def _compute_upto_date_qty(self):
        for line in self:
            line.upto_date_qty = line.pre_qty + line.quantity
            
    @api.multi
    @api.depends('pre_qty', 'price_unit')
    def _compute_pre_amount(self):
        for line in self:
            line.pre_amount = line.pre_qty*line.price_unit
            
            
    @api.multi
    @api.depends('pre_amount', 'price_subtotal')
    def _compute_upto_date_amount(self):
        for line in self:
            line.upto_date_amount = line.pre_amount+line.price_subtotal
            
    @api.multi
    @api.depends('price_unit', 'total_assigned_qty')
    def _compute_total_amount(self):
        for line in self:
            line.total_amount = line.price_unit*line.total_assigned_qty        
        
        
    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
    origin = fields.Char(string='Source Document',
        help="Reference of the document that produced this invoice.")
    sequence = fields.Integer(string='Sequence', default=10,
        help="Gives the sequence of this line when displaying the invoice.")
    invoice_id = fields.Many2one('hiworth.invoice', string='Invoice Reference',
        ondelete='cascade', index=True)
    uos_id = fields.Many2one('product.uom', string='Unit of Measure',
        ondelete='set null', index=True)
    product_id = fields.Many2one('product.product', string='Product',
        ondelete='restrict', index=True)

    price_unit = fields.Float(string='Unit Price', required=True,
        digits= dp.get_precision('Product Price'),
        default=_default_price_unit)
    price_subtotal = fields.Float(string='Amount')
    quantity = fields.Float(string='Quantity', digits= dp.get_precision('Product Unit of Measure'))
    discount = fields.Float(string='Discount (%)', digits= dp.get_precision('Discount'),
        default=0.0)
    invoice_line_tax_id = fields.Many2many('account.tax',
        'hiworth_invoice_line_tax', 'invoice_line_id', 'tax_id',
        string='Taxes')
    state = fields.Selection([
            ('draft','Draft'),
            ('partial','Partially Paid'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
        ], string='Status', readonly=True, default='draft')
    company_id = fields.Many2one('res.company', string='Company',
        related='invoice_id.company_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner',
        related='invoice_id.partner_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        related='invoice_id.currency_id', store=True, readonly=True)
#     task_id = fields.Many2one('project.task', string='Task',
#         related='invoice_id.task_id', store=True, readonly=True)
    date = fields.Date('Date')
    total_assigned_qty = fields.Float('Assigned Qty')
    remarks = fields.Text('Description')
    shd_no = fields.Char('Shd No.')
    pre_qty = fields.Float('Previous Qty')
    upto_date_qty = fields.Float(compute='_compute_upto_date_qty', store=True, string='Up to Date Qty')
    pre_amount = fields.Float(compute='_compute_pre_amount', store=True, string='Previous Amount')
    upto_date_amount = fields.Float(compute='_compute_upto_date_amount', store=True, string='Up to Date Amount')
    total_amount = fields.Float(compute='_compute_total_amount',store=True, string='Total Amount')
    remark = fields.Char('Remarks')
    
    work_order_id = fields.Many2one(related='invoice_id.work_order_id', store=True, string="Work Order")
    stage_id = fields.Many2one('stage.line.prime','Stage')

    @api.onchange('stage_id','price_unit','total_assigned_qty','price_subtotal')
    def _onchange_stages(self):
        if self.stage_id and self.total_amount !=0:
            if self.stage_id.approximated_amnt < self.price_subtotal:
                self.price_subtotal = 0
                print "self.stage_id.id===========", self.stage_id
                return {
                    'warning': {
                                'title': 'Warning',
                                'message': "The Amount Exceeds The Stage Total Limit"
                                    }
                                }

    
    
    
    
#     @api.model
#     def create(self,vals):
# #         print 'self============================',vals['invoice_id'],rgrfsfdf
# #         if vals['invoice_id']:
#         print 'asdddd================== ',self.invoice_id,self.env['hiworth.invoice'].search([('id','=',vals['invoice_id'])])
#         self.env['hiworth.invoice'].search([('id','=',vals['invoice_id'])]).compute_state__get()
#             
#         return super(hiworth_invoice_line, self).create(vals)
    
    @api.onchange('price_subtotal')
    def amount_change(self):
#         print 'aaaaaaaaaaaa=============='
        if self.price_unit != 0.0 and self.price_subtotal != 0.0:
            self.quantity = self.price_subtotal/self.price_unit
            
    @api.onchange('price_unit','quantity')
    def quantity_change(self):
        if self.price_unit != 0.0 and self.price_subtotal != 0:
            self.price_subtotal = float(str(round(self.quantity*self.price_unit, 2)))
        
        
    
    @api.onchange('product_id')
    def product_id_change(self):

        if self.partner_id.id == False:
            raise except_orm(_('No Partner Defined!'), _("You must first select a partner."))
        if self.invoice_id.work_order_id.id == False:
            raise except_orm(_('No Work Order Selected!'), _("You must first select a Work Order."))
        values = {}
        
        
#         if uom_id:
#             uom = self.env['product.uom'].browse(uom_id)
#             if product.uom_id.category_id.id == uom.category_id.id:
#                 values['uos_id'] = uom_id

#         dom/ain = {'uos_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        self.company = self.env['res.company'].browse(self.company_id.id)
        self.currency = self.env['res.currency'].browse(self.currency_id.id)

#         if company and currency:
#             if company.currency_id != currency:
#                 values['price_unit'] = values['price_unit'] * currency.rate
# 
#             if values['uos_id'] and values['uos_id'] != product.uom_id.id:
#                 values['price_unit'] = self.env['product.uom']._compute_price(
#                     product.uom_id.id, values['price_unit'], values['uos_id'])
                    
#         order_lines = self.env['work.order.line'].search([('work_order_id','=',self.invoice_id.work_order_id.id)]) 
        if self.product_id.id != False:
            product_spec = self.env['work.order.line'].search([('work_order_id','=',self.invoice_id.work_order_id.id),('product_id','=',self.product_id.id)])[0]
#             print 'product_spec========================', product_spec
            self.uos_id = product_spec.uom_id.id
            self.remarks = product_spec.remarks
            self.price_unit =  product_spec.rate
            self.name = product_spec.product_id.name
            self.total_assigned_qty = product_spec.qty
        
#         invoice_lines = [] 
        invoice_lines = self.env['hiworth.invoice.line'].search([('work_order_id','=',self.work_order_id.id),('product_id','=',self.product_id.id),('state','!=','cancel')])
        print 'invoice_lines============================', invoice_lines
        pre_qty = 0.0
        for invoice_line in invoice_lines:
            pre_qty += invoice_line.quantity
        self.pre_qty = pre_qty
        
        product_ids = []
        if self.invoice_id.work_order_id.id != False:
#             print 'test======================',task_id,product
            order_lines = self.env['work.order.line'].search([('work_order_id','=',self.invoice_id.work_order_id.id)]) 
            product_ids = [order_line.product_id.id for order_line in order_lines]
            return {'domain': {'product_id': [('id','in',product_ids)]}}
      
    @api.onchange('quantity')
    def _onchange_qty(self):
        if self.quantity > self.total_assigned_qty-self.pre_qty:
            self.quantity = self.total_assigned_qty-self.pre_qty
            return {
                    'warning': {
                                'title': 'Warning',
                                'message': "Qty is greater than Qty to be invoiced."
                                    }
                                }
            

#             task_id = self.invoice_id.task_id
# #             print 'task_id===================', self.invoice_id,self.invoice_id.task_id 
#              
#             estimation = self.env['project.task.estimation'].search([('task_id','=',task_id.id),('pro_id','=',self.product_id.id)])
# #             print 'estimation========================', estimation
#             if estimation.invoiced_qty == 0.0:
#                 if estimation.qty == 0.0:
#                     self.quantity = 0.0
#                     return {
#                         'warning': {
#                                 'title': 'Warning',
#                                 'message': "Please enter some Qty in the Estimation."
#                                     }
#                                 }
#                 if estimation.qty < self.quantity:
#                     self.quantity = estimation.qty
# #                     estimation.write({'invoiced_qty': self.quantity})
#                     return {
#                         'warning': {
#                                 'title': 'Warning',
#                                 'message': "Entered qty is greater than the qty to invoice."
#                                     }
#                                 }
#                 if estimation.qty > self.quantity:
#                     print 'qweqeqweqeqwe'
# #                     estimation.write({'invoiced_qty': self.quantity})
# #                 print 'estimation=======================', estimation,estimation.invoiced_qty   
#             if estimation.invoiced_qty != 0.0:
#                 if self.quantity > estimation.qty - estimation.invoiced_qty:
#                     self.quantity = estimation.qty - estimation.invoiced_qty
# #                     print 'asdasd========================', self.quantity
#                     return {
#                         'warning': {
#                                 'title': 'Warning',
#                                 'message': "Entered qty is greater than the qty to invoice."
#                                     }
#                                 }
#                             
        
class hiworth_invoice_line2(models.Model):
    _name = 'hiworth.invoice.line2'
        
    @api.one
    @api.depends('price_unit', 'discount', 'quantity',
        'product_id')
    def _compute_price(self):
        for line in self:
            line.price_subtotal = line.price_unit*line.quantity    
    
    name = fields.Char('Name')
    invoice_id = fields.Many2one('hiworth.invoice', string='Invoice Reference',
        ondelete='cascade', index=True)
    uos_id = fields.Many2one('product.uom', string='Unit of Measure',
        ondelete='set null', index=True)
    product_id = fields.Many2one('product.product', string='Product',
        ondelete='restrict', index=True)

    price_unit = fields.Float(string='Unit Price', required=True,
        digits= dp.get_precision('Product Price'))
    price_subtotal = fields.Float(string='Amount', digits= dp.get_precision('Account'),
        store=True, readoinvoice_idnly=True, compute='_compute_price')
    quantity = fields.Float(string='Quantity', digits= dp.get_precision('Product Unit of Measure'))
    discount = fields.Float(string='Discount (%)', digits= dp.get_precision('Discount'),
        default=0.0)
    
    company_id = fields.Many2one('res.company', string='Company',
        related='invoice_id.company_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner',
        related='invoice_id.partner_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        related='invoice_id.currency_id', store=True, readonly=True)
    task_id = fields.Many2one('project.task', 'Task')
    location_id = fields.Many2one(related='task_id.project_id.location_id', string="Location")
    
    
    
    
    
    
    