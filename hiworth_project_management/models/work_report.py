from openerp import models, fields, api, _
import datetime
from datetime import time

class WorkReportCommentAndReply(models.Model):

	_name = 'comment.reply'

	comment = fields.Text('Comment Box')
	work_report_id = fields.Many2one('work.report')

	@api.one
	def comment_and_reply(self):
		self.env['popup.notifications'].create({
			'name': self.work_report_id.to_id.id,
			'status': 'draft',
			'message': "Work Status Comment "+self.comment})

class WorkReport(models.Model):
	_name = 'work.report'
	_order = 'id desc'
	_rec_name = 'date_today'

	task_id = fields.Many2one('event.event','Task Number')
	from_id = fields.Many2one('res.users',string="From")
	report = fields.Text('Report')
	notes = fields.Text('Notes')
	date_today = fields.Datetime('Date',default=lambda self: fields.datetime.now())
	customer_id = fields.Many2one('res.partner','Customer',related="project.partner_id")
	project = fields.Many2one('project.project','Project')
	state = fields.Selection([('draft','Draft'),('validate','Validated'),('transfer','Approved'),('send','Sent'),('approved','Approved')],default="draft")

	customer_nick = fields.Char('Customer Nick Name',related="project.nick_name",readonly=True)
	to_id = fields.Many2one('res.users',string="To", readonly=True)
	date_end = fields.Datetime('Default End Date',store=True)
	normal_end = fields.Datetime('Completed On')
	req_end = fields.Boolean(default=False)
	user_id = fields.Many2one('res.users','Send By',readonly=True)
	sent_report = fields.Many2one('res.users','Send Report')
	manager = fields.Many2one('res.users','Manager')
	work_report = fields.Boolean(default=False)
	validated = fields.Many2one('res.users')
	status = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	status_admin = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	status_sent = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	branch_id = fields.Many2one('res.company','Branch')
	comment_line = fields.One2many('comment.reply','work_report_id')



	_defaults = {
		'user_id':lambda obj, cr, uid, ctx=None: uid,
		'to_id' :lambda obj, cr, uid, ctx=None: 1, 
		'branch_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'ir.attachment', context=c),
		}

	@api.multi
	def comment_reply(self):
		# print "=-=-=-===-=--"
		dummy, view_id = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'comment_reply_form')
		print view_id
		return {
			'name': _('Lead'),
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'comment.reply',
			'view_id': view_id,
			'type': 'ir.actions.act_window',
			'target': 'new',
			'context': {
                'default_work_report_id': self.id
			}
		}

	@api.onchange('project')
	def onchange_project(self):
		if self.project:
			if not self.branch_id:
				self.branch_id = self.project.company_id.id

	@api.onchange('task_id')
	def onchange_task_id(self):
		if self.task_id:
			self.date_end = self.task_id.date_end
			self.project = self.task_id.project_id.id
			self.manager = self.task_id.project_id.user_id.id
			if not self.branch_id:
				self.branch_id = self.task_id.project_id.company_id.id 

	# @api.multi
	# def get_notifications(self):
	# 	result = []
	# 	for obj in self:
	# 		result.append({
	# 			'sent_report':obj.sent_report.name,
	# 			'to_id':obj.to_id.name,
	# 			'user_id':obj.user_id.name,
	# 			'manager':obj.project.user_id.name,
	# 			'status': obj.status,
	# 			'status_admin': obj.status_admin,
	# 			'status_sent': obj.status_sent,
	# 			'id': obj.id,
	# 			'state':obj.state,
	# 			'validated':obj.validated.name
	# 		})
	# 	return result

	@api.model
	def create(self, vals):
		if vals.get('task_id'):
			vals['date_end'] = self.env['event.event'].search([('id','=',vals.get('task_id'))]).date_end
			vals['project'] = self.env['event.event'].search([('id','=',vals.get('task_id'))]).project_id.id
			vals['manager'] = self.env['event.event'].search([('id','=',vals.get('task_id'))]).project_id.user_id.id
		result = super(WorkReport, self).create(vals)
		result.task_id.report_id = result.id
		user_ids = []
			# user_ids.append(self.user_id.id)
		dgm = self.env.ref("hiworth_project_management.group_dgm")
		for user in dgm.users:
			if user.company_id.id == result.user_id.company_id.id and user.id not in user_ids:
				user_ids.append(user.id)
		gm = result.env.ref("hiworth_project_management.group_general_manager")
		for user in gm.users:
			if user.id not in user_ids:
				user_ids.append(user.id)
			for user in user_ids:
			# print 'user==============', user
				self.env['popup.notifications'].sudo().create({
													'name':user,
													'message':"You have daily report to validate from "+str(result
														.user_id.name),
													'status':'draft',
					})
		return result

	@api.multi
	def send_report_user(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_project_send_document_wizard')
		view_id = view_ref[1] if view_ref else False
		res = {
		   'type': 'ir.actions.act_window',
		   'name': _('Send Report'),
		   'res_model': 'transfer.document',
		   'view_type': 'form',
		   'view_mode': 'form',
		   'view_id': view_id,
		   'target': 'new',
		   'context': {'default_recs':self.id}
	   }

		return res

	@api.multi
	def send_report(self):
		if self.work_report == False:
			if self.state == 'validate' or self.state == 'send':
				self.state = 'approved'
				if self.sent_report:
					if self.sent_report.id == self.env.uid:
						rec = self.env['res.groups'].sudo().search([('name','=','Daily Report - Approve Button')])
						if rec:
							list = []
							for users in rec.users:
								if users.id != self.env.user.id:
									list.append(users.id)
							rec.users = [(6, 0, list)]
			if self.state == 'draft':
				user_ids = []
				dgm = self.env.ref("hiworth_project_management.group_dgm")
				for user in dgm.users:
					if user.company_id.id == self.user_id.company_id.id and user.id not in user_ids:
						user_ids.append(user.id)
				gm = self.env.ref("hiworth_project_management.group_general_manager")
				for user in gm.users:
					if user.id not in user_ids:
						user_ids.append(user.id)
					for user in user_ids:
						self.env['popup.notifications'].sudo().create({
															'name':user,
															'message':"You have daily report to Approve from "+str(self.user_id.name),
															'status':'draft',
							})
				self.validated = self.env.user.id
				self.normal_end = datetime.datetime.now()
				self.task_id.completion_time = datetime.datetime.now()
				self.state = 'validate'
				if self.project:
					self.state = 'validate'
			
		else:
			if self.state == 'validate':
				self.sent_report = self.env['res.users'].search([('partner_id','=',self.customer_id.id)]).id
				self.state = 'transfer'
			if self.state == 'draft':
				self.state = 'validate'
				self.validated = self.env.user.id


