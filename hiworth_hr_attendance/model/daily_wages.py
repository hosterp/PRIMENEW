from openerp import models, fields, api
from datetime import datetime, timedelta


class DailyWages(models.Model):
	_name = 'daily.wages'

	date_from = fields.Date('Period From')
	date_to = fields.Date('Period To',compute="_onchange_date_from")
	daily_wage = fields.One2many('daily.wages.line','daily_id',string='Daily Wages')


	@api.multi
	@api.depends('date_from')
	def _onchange_date_from(self):
		for line in self:
			if line.date_from:
				line.date_to = datetime.strptime(line.date_from, "%Y-%m-%d") + timedelta(days=5)


class DailyWagesLine(models.Model):
	_name = 'daily.wages.line'

	daily_id = fields.Many2one('daily.wages')
	employee = fields.Many2one('hr.employee','Worker',domain=[('status1','=','active')])
	employee_type = fields.Char('Worker Type',compute="_get_employee_type")
	days = fields.Integer('No Of Days Present',compute="_get_no_days")
	advance = fields.Float('Advance',compute="_get_no_days")
	amount = fields.Float('Total Wage',compute="_get_employee_type")
	# location = fields.Many2one('stock.location','location',compute="onchange_employee_name")
	wage = fields.Float('Wage Per Day')

	@api.multi
	@api.depends('daily_id')
	def _get_no_days(self):
		for line in self:
			count = 0
			amount = 0
			if line.employee:
				date_from = datetime.strptime(line.daily_id.date_from, "%Y-%m-%d").date()
				date_to = datetime.strptime(line.daily_id.date_to, "%Y-%m-%d").date()
				temp_date = date_from
				while(temp_date <= date_to): 
					recs = self.env['hiworth.hr.attendance'].search([('name','=',line.employee.id)])
					for val in recs:
						date = datetime.strptime(val.sign_in, "%Y-%m-%d %H:%M:%S").date()
						if date == temp_date:
							count += 1
					adv = self.env['advance.pay'].search([('date','=',temp_date)])
					for payline in adv:
						for pay in payline.advance_line:
							if pay.employee.id == line.employee.id:
								amount += pay.amount


					temp_date = temp_date + timedelta(days=1)
			line.days = count
			line.advance = amount
			


	@api.multi
	@api.depends('employee','days','wage','advance')
	def _get_employee_type(self):
		for line in self:
			line.amount = 0 
			if line.employee:
				if line.employee.worker_type == 'helper':
					line.employee_type = 'Helper'
				if line.employee.worker_type == 'mason':
					line.employee_type = 'Mason'
				line.amount += ((line.days*line.wage)-line.advance)



	@api.onchange("employee")
	def onchange_employee(self):
		record = self.env['hr.employee'].search([('worker_type','in',('mason','helper'))])
		ids = []
		for item in record:
			ids.append(item.id)
		# print "idsssssssssssssssssss", ids
		return {'domain': {'employee': [('id', 'in', ids)]}}

	# @api.one
	# @api.depends("employee")
	# def onchange_employee_name(self):
	# 	for line in self:
	# 		if line.employee:
	# 			record = self.env['hiworth.hr.attendance'].search([('name','=',line.employee.id),('sign_in','>=',self.daily_id.date),('sign_out','<=',self.daily_id.date)])
	# 			if record:
	# 				line.location = record.location.id