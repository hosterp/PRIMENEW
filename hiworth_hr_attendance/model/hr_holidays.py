from openerp import models, fields, api,_
from openerp.exceptions import except_orm, ValidationError


class ApprovedPersons(models.Model):
	_name = 'approved.persons'

	name = fields.Many2one('res.users')
	app_id = fields.Many2one('hr.holidays')
	date_today = fields.Datetime('Date')

class HrHolidays(models.Model):
	_inherit = 'hr.holidays'
	_order = 'id desc'

	status = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	# admin = fields.Many2one('res.users', string='Admin')
	next_approver = fields.Many2one('res.users',readonly=True)
	approved_by = fields.Many2one('res.users')
	approved_persons = fields.One2many('approved.persons','app_id',readonly=True)
	state = fields.Selection([('draft', 'To Submit'), ('cancel', 'Cancelled'),('confirm', 'To Approve'),('validated','Validated'), ('refuse', 'Refused'), ('validate1', 'Second Approval'), ('validate', 'Approved')],
			'Status', readonly=True, copy=False, default="draft")

	@api.multi
	def validate_leave(self):
		list = []
		
		self.approved_by = self.env.user.id
		self.state = 'validate'

		# if self.next_approver:
		# 	if self.env.user.id == self.next_approver.id or self.env.user.id == 1:
		# 		rec = self.env['approved.persons'].create({'date_today':fields.Datetime.now(),
		# 												   'name':self.next_approver.id,
		# 												   'app_id':self.id})
				
		# 		list.append(rec.id)
		# 		for ids in self.approved_persons:
		# 			list.append(ids.id)
		# 		if self.next_approver.employee_id.parent_id.id:
		# 			self.next_approver = self.next_approver.employee_id.parent_id.id
		# 		else:
		# 			if self.next_approver.id == 1:
		# 				self.state = 'validated'
		# 			self.next_approver = False

		# 		self.sudo().write({'approved_persons':[(6,0,list)],'status':'draft'})
		# 	else:
		# 		raise except_orm(_('Warning'),
		# 					 _('You are not the next approver'))



	@api.model
	def create(self,vals):		
		result = super(HrHolidays, self).create(vals)		
		if result.type == 'remove':
			if result.employee_id.parent_id:
				user = self.env['res.users'].search([])
				for u in user:
					if u.has_group('hiworth_project_management.group_admin1') or u.has_group('hiworth_project_management.group_admin2') or u.has_group('hiworth_project_management.group_general_manager') or u.has_group('hiworth_project_management.group_dgm'):
				# if user:
				# 	print "user========================",result.next_approver
				# 	result.next_approver = user.id
				# if result.next_approver:
						self.env['popup.notifications'].create({
								  'name':u.id,
								  'status': 'draft',
								  'message': "You have a leave request to approve from "+str(result.employee_id.name)})
		return result

	@api.multi
	def write(self, vals):
		result = super(HrHolidays, self).write(vals)
		if vals.get('employee_id') and vals.get('type') == 'remove':
			if result['employee_id'].parent_id:
				user = self.env['res.users'].sudo().search([('employee_id','=',result['employee_id'].parent_id.id)])
				if user:
					result['next_approver'] = user.id

		return result


	# _defaults = {
 #        'admin':lambda obj, cr, uid, ctx=None: 1,
 #        }

	@api.multi
	def get_notifications(self):
		result = []
		for obj in self:
			result.append({
				# 'admin':obj.admin.name,
				'status': obj.status,
				'employee_id':obj.employee_id.name,
				'id': obj.id,
				'next_approver': obj.next_approver.name
			})
		return result