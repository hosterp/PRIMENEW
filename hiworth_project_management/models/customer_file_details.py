from openerp import models, fields, api, _

class TransferDocument(models.Model):
	_name = 'transfer.document'

	rec = fields.Many2one('customer.file.details')
	partner_id = fields.Many2one('res.partner','Transfer To')
	user_id = fields.Many2one('res.users','Send To')
	recs = fields.Many2one('work.report')


	@api.onchange('partner_id')
	def onchange_partner_id(self):
		ids = []
		# print "ccccccccccccccccc"
		record = self.env['res.partner'].sudo().search([('is_company','=',False)])
		# print "dddddddddddddd", record

		for item in record:
			ids.append(item.id)
		return {'domain': {'partner_id': [('id', 'in', ids)]}}

	@api.multi
	def send_doc(self):
		if self.user_id:
			self.recs.sent_report = self.user_id.id
			self.recs.project.work_report_man = self.user_id.id
			self.recs.state = 'send'
			rec = self.env['res.groups'].search([('name','=','Daily Report - Approve Button')])
			if rec:
				rec.users = [(6, 0, [self.user_id.id])]


	@api.multi
	def transfer_doc(self):
		if self.partner_id:
			if self.partner_id.customer == True:
				self.rec.write({'state': 'pend_cust'})
				self.env['popup.notifications'].sudo().create(
														{
														'name':self.rec.logged_user.id,
														'status':'draft',
														'message':"You have a file to approve",
														})

			else:

				self.env['customer.file.details'].sudo().create({
					'name':self.env['ir.sequence'].next_by_code('customer.file.details') or '/',
					'partner_id':self.rec.partner_id.id,
					'project_id':self.rec.project_id.id,
					'logged_user':self.env['res.users'].search([('partner_id','=',self.partner_id.id)]).id,
					'date_today':fields.Date.today(),
					'transfer':self.rec.id,
					'state':'pending',
					'owner_id':self.rec.logged_user.id,
					'file_details':self.rec.file_details,
					'branch_id':self.rec.branch_id.id

					})
				print "eeeeeeeeeeeeeeeeeeeeeee",self.rec.logged_user.name
				self.rec.write({'state': 'waiting',
								'owner_id':self.rec.logged_user.id,
								'transfer_buddy':self.env['res.users'].search([('partner_id','=',self.partner_id.id)]).id,})



class CustomerFileDetails(models.Model):
	_name = 'customer.file.details'
	_order = 'id desc'

	name = fields.Char()
	partner_id = fields.Many2one('res.partner', string='Customer Name', required=True)
	project_id = fields.Many2one('project.project', string="Project")
	date_today = fields.Date(string='Date')
	logged_user = fields.Many2one('res.users','Employee/Manager')
	file_location = fields.Char('File Location')
	remarks = fields.Text('Remarks')
	file_details = fields.Char('File Details')
	transfer = fields.Many2one('customer.file.details')
	transfer_buddy = fields.Many2one('res.users')
	to_customer = fields.Many2one('res.users')
	admin = fields.Many2one('res.users')
	state = fields.Selection([('draft','Draft'),('waiting','Waiting'),('pend_cust','For Admin Approval'),('transfer','Transferred'),('pending','Pending'),('accept','Accepted')],default='draft')
	status = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	status_admin = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	branch_id = fields.Many2one('res.company', string='Branch')
	owner_id = fields.Many2one('res.users',"Transfered From")

	@api.onchange('project_id')
	def onchange_project_id(self):
		if self.project_id:
			self.branch_id = self.project_id.company_id.id
		

	@api.onchange('partner_id')
	def onchange_partner_id(self):
		# if self.partner_id:
		# 	self.branch_id = self.env.user.company_id.id
		ids = []
		record = self.env['res.partner'].sudo().search([('is_cus','=',True)])

		for item in record:
			ids.append(item.id)
		return {'domain': {'partner_id': [('id', 'in', ids)]}}
		
   

	@api.multi
	def get_notifications(self):
		result = []
		for obj in self:
			result.append({
				'logged':obj.logged_user.name,
				'admin':obj.admin.name,
				'status': obj.status,
				'id': obj.id,
				'status_admin':obj.status_admin,
				'partner':obj.partner_id.name
			})
		return result


	_defaults = {
		'logged_user':lambda obj, cr, uid, ctx=None: uid,
		'admin': lambda obj, cr, uid, ctx=None: 1
		}


	@api.model
	def create(self, vals):
		result = super(CustomerFileDetails, self).create(vals)
		result.date_today = fields.Date.today()
		if result.state == 'pending':
			self.env['popup.notifications'].sudo().create(
														{
														'name':result.logged_user.id,
														'status':'draft',
														'message':"You have a file to accept",
														})
		# result.branch_id = self.env.user.company_id.id
		if result.name == False:
			result.name = self.env['ir.sequence'].next_by_code('customer.file.details') or '/'
		return result


	@api.multi
	def transfer_document(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_project_transfer_document_wizard')
		view_id = view_ref[1] if view_ref else False
		res = {
		   'type': 'ir.actions.act_window',
		   'name': _('Transfer Document'),
		   'res_model': 'transfer.document',
		   'view_type': 'form',
		   'view_mode': 'form',
		   'view_id': view_id,
		   'target': 'new',
		   'context': {'default_rec':self.id}
	   }

		return res

	@api.multi
	def accept_document(self):
		self.state = 'accept'
		self.transfer.sudo().write({'state': 'transfer','logged_user':self.logged_user.id,
			'owner_id':self.owner_id.id})

	@api.multi
	def approve_file(self):
		self.state = 'transfer'
		self.to_customer = self.logged_user.id
		self.logged_user = self.env['res.users'].search([('partner_id','=',self.partner_id.id)]).id
