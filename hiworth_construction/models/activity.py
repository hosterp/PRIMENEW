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


class project_attachment(models.Model):
    _inherit = 'project.attachment'
    
    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None: 
            context = {}
        line_num = 1    
    
        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context) 
            for line_rec in first_line_rec.activity_id.attachment_ids: 
                line_rec.line_no = line_num 
                line_num += 1 

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    activity_id = fields.Many2one('activity.activity', 'Activity')

class ActivityActivity(models.Model):
    _name = 'activity.activity'
    _order = 'date desc'
    
    name = fields.Char('Name')
    date = fields.Date('Date')
    attachment_ids = fields.One2many('project.attachment', 'activity_id', 'Attachments')
    remark = fields.Text('Remarks')
    state = fields.Selection([('draft', 'Draft'),
                                   ('progress', 'Progress'),
                                   ('completed', 'Completed'),
                                   ('cancel', 'Cancelled')
                                   ], 'Status', readonly=True, select=True, copy=False, default='draft')
                                   
    @api.multi
    def action_start(self):
        self.state = 'progress'
        
    @api.multi
    def action_done(self):
        self.state = 'completed'
        
    @api.multi
    def action_cancel(self):
        self.state = 'cancel'
        
    
                                   