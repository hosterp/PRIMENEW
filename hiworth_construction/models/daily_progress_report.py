from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
import time
from datetime import datetime
import datetime
from openerp.exceptions import except_orm, Warning, RedirectWarning
#from openerp.osv import fields
from openerp import tools
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from pychart.arrow import default
from cookielib import vals_sorted_by_key
# from pygments.lexer import _default_analyse
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
# from openerp.osv import osv
from openerp import SUPERUSER_ID

from lxml import etree


class daily_progress_report(models.Model):
    _name = 'daily.progress.report'
    _order = 'date desc'
    
    
    
    name = fields.Char('Name')
    date = fields.Date('Date')
#     user_id = fields.Many2one('res.partner', 'Engineer', domain=[('customer','=',False),('supplier','=',False),
#                                                                 ('contractor','=',False)])
    remark = fields.Text('Remarks')
    dpr_line_ids = fields.One2many('daily.progress.report.line', 'report_id', 'Lines')
    inspect1 = fields.Many2one('hr.employee', 'Inspector1',domain=[('status1','=','active')])
    inspect2 = fields.Many2one('hr.employee', 'Inspector2',domain=[('status1','=','active')])
    inspect3 = fields.Many2one('hr.employee', 'Inspector3',domain=[('status1','=','active')])
    inspect4 = fields.Many2one('hr.employee', 'Inspector4',domain=[('status1','=','active')])
    
    _defaults = {
        'date': date.today()
        }
    
class daily_progress_report_line(models.Model):
    _name = 'daily.progress.report.line'
    
    @api.multi
    @api.onchange('date')
    def onchange_date(self):
        self.date = self.report_id.date
        
    name = fields.Char('Name')
    project_id = fields.Many2one('project.project', 'Project')
    partner_id = fields.Many2one('res.partner', 'Contractor', domain=[('contractor','=',True)])
    report_id = fields.Many2one('daily.progress.report', 'Report')
    date = fields.Date('Date')
#     activity = fields.Text('Name of the Work')
    qty1 = fields.Float('Qty')
    qty2 = fields.Float('Qty')
    qty3 = fields.Float('Qty')
    qty4 = fields.Float('Qty')
    category = fields.Char('Category')
    nos = fields.Float('Nos.')
    rate = fields.Char('Rate')
    amount = fields.Float('Amount')
    remarks = fields.Text('Remarks')
        
    
                                   