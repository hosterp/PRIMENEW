from openerp import models, fields, api

class Res_users(models.Model):
	_inherit = 'res.users'

	employee_id = fields.Many2one('hr.employee','Related Employee',domain=[('status1','=','active')])