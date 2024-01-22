from openerp import models, fields, api


class ResCompany(models.Model):
    _inherit = 'res.company'
    
    gst_no = fields.Char('GST No')
    pan_no = fields.Char('PAN No')