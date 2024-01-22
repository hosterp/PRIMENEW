from openerp import models, fields, api

class AdvancePay(models.Model):
	_name = 'advance.pay'

	date = fields.Date('Date')
	advance_line = fields.One2many('advance.pay.line','adv_id')

class AdvancePayLine(models.Model):
	_name = 'advance.pay.line'

	adv_id = fields.Many2one('advance.pay')
	employee = fields.Many2one('hr.employee','Employee',domain=[('status1','=','active')])
	amount = fields.Float('Advance')


	# @api.onchange("employee")
	# def onchange_employee(self):
	# 	record = self.env['hr.employee'].search([('worker_type','in',('mason','helper'))])
	# 	ids = []
	# 	for item in record:
	# 		ids.append(item.id)
	# 	# print "idsssssssssssssssssss", ids
	# 	return {'domain': {'employee': [('id', 'in', ids)]}}