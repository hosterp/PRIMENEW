from openerp import models, fields, api


class AttendanceRequest(models.Model):
	_name = 'attendance.request'

	date = fields.Date('Requested Date',default=fields.Date.today())
	sign_in = fields.Datetime('Requested Sign In',required=True)
	sign_out = fields.Datetime('Requested Sign Out',required=True)
	user = fields.Many2one('res.users','Logged User')

	_defaults = {
		'user':lambda obj, cr, uid, ctx=None: uid,
		}

	@api.one
	def request_attendance(self):
		self.ensure_one()
		if self.sign_in and self.sign_out:
			
			self.env['pending.attendance.request'].create({'date':self.date,
												   'sign_in':self.sign_in,
												   'sign_out':self.sign_out,
												   'user1':self.user.employee_id.id})
			# if self.user.employee_id.parent_id:
			# 	print "=========================employee_id", self.user.employee_id.parent_id.id
			# 	related_user = self.env['res.users'].search([('employee_id', '=', self.user.employee_id.parent_id.id)])
			user = self.env['res.users'].search([])
			for u in user:
				if u.has_group('hiworth_project_management.group_admin1') or u.has_group('hiworth_project_management.group_admin2') or u.has_group('hiworth_project_management.group_general_manager') or u.has_group('hiworth_project_management.group_dgm'):	
					self.env['popup.notifications'].create({
							  'name': u.id,
							  'status': 'draft',
							  'message': "You have a attendance request to approve"})
			return

class PendingRequests(models.Model):
	_name = 'pending.attendance.request'
	_rec_name = 'user1'

	date = fields.Date('Requested Date')
	sign_in = fields.Datetime('Sign In')
	sign_out = fields.Datetime('Sign Out')
	user1 = fields.Many2one('hr.employee','Logged User', domain=[('status1','=','active')])
	state = fields.Selection([('pending','Pending'),('approved','Approved')],default="pending")
	approved_by = fields.Many2one('res.users')

	@api.multi
	def approve_attendance(self):
		self.approved_by = self.env.user.id 
		self.state = 'approved'
		self.env['hiworth.hr.attendance'].with_context(default_name=self.user1.id,default_check=1).create({
												  'name':self.user1.id,
												  'sign_in':self.sign_in,
												  'sign_out':self.sign_out,
												  'state':'sign_in',
												  'employee_type':self.user1.employee_type,
												  'attendance_signin_id':0,
												  'attendance_signout_id':0,
												  })



