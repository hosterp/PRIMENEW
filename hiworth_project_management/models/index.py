from openerp import models, fields, api,_
from openerp.osv import expression


class ProjectProject(models.Model):
	_inherit = 'project.project'



	initial_meeting_date = fields.Date('Initial Meeting Date')
	pba_no = fields.Char('Project Number')
	client_id = fields.Char('Client Id')
	work_nature = fields.Char('Nature Of Work')
	building_nature = fields.Char('Type Of Building')
	permit_authority = fields.Char('Permitting Authority')
	permit_no = fields.Char('Permit Number')
	permit_from = fields.Date('Permit Validity')
	permit_to = fields.Date('Permit To')
	direction = fields.Char('Direction')
	area = fields.Char('Initial Area Limit')
	# area_plot = fields.Float('Area Of Plot')
	plote_data = fields.Text('Initial Plot Datas & Req')
	survey_no = fields.Char('Survey Number')
	type_of_deed = fields.Char('Type of Deed')
	sub_registrar_office = fields.Char('Sub Registrar Office')
	extend = fields.Char('Extend')
	deed_no = fields.Char('Deed Number')
	ward_no = fields.Char('Ward Number')
	no_story = fields.Char('No Of Stories')
	my_remarks = fields.Text('Remarks')
	external_user = fields.Boolean('External User', default=False)
	user = fields.Many2one('res.users', 'Assigned to')
	nick_name = fields.Char('Nick Name',related="partner_id.nick_name")
	dob = fields.Date('DOB',related="partner_id.dob")
	occupation = fields.Char('Occupation',related="partner_id.occupation")
	street1 = fields.Char('Street',related="partner_id.street1")
	street3 = fields.Char('Post Office',related="partner_id.street3")
	city1 = fields.Char('City',related="partner_id.city1")
	state_id1 = fields.Many2one('res.country.state',related="partner_id.state_id1")
	country_id1 = fields.Many2one('res.country',related="partner_id.country_id1")
	zip1 = fields.Char('Zip',related="partner_id.zip1")
	wife_hus = fields.Char('Wife/Husband',related="partner_id.wife_hus")
	dob_wh = fields.Date('DOB',related="partner_id.dob_wh")
	# children = fields.One2many('children.details','children_id')
	# wdng_day = fields.Date('Wedding Anniversary Date',related="partner_id.wdng_day")
	wdng_d = fields.Selection(related="partner_id.wdng_d", string='Day')
	wdng_m = fields.Selection(related="partner_id.wdng_m", string='Month')

	street = fields.Char('Street',related="partner_id.street")
	street2 = fields.Char('Post Office',related="partner_id.street2")
	city = fields.Char('City',related="partner_id.city")
	state_id = fields.Many2one('res.country.state')
	country_id = fields.Many2one('res.country',related="partner_id.country_id")
	zip = fields.Char('Zip')
	email = fields.Char(related="partner_id.email")
	phone= fields.Char(related="partner_id.phone")
	mobile = fields.Char(related="partner_id.mobile")
	village = fields.Char('Village')
	taluk = fields.Char('Taluk')
	district = fields.Char('District')
	building_no = fields.Char('Number of Nearest Building')
	local_body = fields.Selection([('panchayathu','PANCHAYATHU'),('muncipality','MUNCIPALITY'),('corporation','CORPORATION')],string="Local Body")
	latitude = fields.Float('latitude',digits=(16,5))
	longitude = fields.Float('longitude',digits=(16,5))
	permit_date = fields.Date('Permit Date')
	file_submitted_on = fields.Date('File Submitted')
	fire_noc = fields.Boolean('Fire NOC')
	fire_noc_remark = fields.Text('Fire NOC Remarks')
	other_permits = fields.Text('Other Permits')

	north = fields.Char('North')
	east = fields.Char('East')
	west = fields.Char('West')
	south = fields.Char('South')

	inbox_one2many = fields.One2many('project.customer.inbox', 'project_id', string='Inbox')
	sent_one2many = fields.One2many('project.customer.sent', 'project_sent_id', string='Sent Messages')

	project_details = fields.Selection([
			('client','Client Details'),
			('project','Project Details'),
			('office','Office Management'),
			('site','Site Management'),
			('accounts','Accounts'),
			('messaging','Messaging'),
		], string='Details')

	@api.onchange('user_id')
	def onchange_user_id(self):
		ids = []
		emp_list = []
		employees = self.env['hr.employee'].search([('status1','=','active')])
		for emp_id in employees:
			if emp_id.user_category.id == self.env.ref('hiworth_project_management.group_employee').id:
				emp_list.append(emp_id.id)
		record = self.env['res.users'].search([('employee_id','in',emp_list)])

		for item in record:
			ids.append(item.id)
		return {'domain': {'user_id': [('id', 'in', ids)]}}

	@api.multi
	def show_google_map(self):
		myurl='https://www.google.co.in/maps/@{},{},15z'.format(self.latitude,self.longitude),
		return {
				'name':"google",

				'type':'ir.actions.act_url',
				
				'target':'new',
				'url':myurl

		}



	@api.multi
	def open_wizard_project_details(self):
		# self.bool_msg = True
		# self.state = 'pending'
		# ids = self.from_id.id
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'form_project_wizard_prime')
		view_id = view_ref[1] if view_ref else False
		project = self.env['project.project'].search([('partner_id','=', self.partner_id.id),('pba_no','=',self.pba_no)])
		res = {
		   'type': 'ir.actions.act_window',
		   'name': _('Details'),
		   'res_model': 'project.project',
		   'view_type': 'form',
		   'view_mode': 'form',
		   'view_id': view_id,
		   'target': 'new',
		   'res_id': project.id,
		   'context': {'default_partner_id': self.partner_id.id,'default_name': self.name}
	   }
	 
		return res


	@api.onchange('project_details')
	def onchange_customer_message(self):
		if self.project_details == 'messaging':
			inbox_list=[]
			sent_list=[]
			inbox_id = self.env['im_chat.message.req'].search([('to_id','=', self.env['res.users'].search([('partner_id','=',self.partner_id.id)])[0].id)])
			for inbox in inbox_id:
				inbox_list.append((0, False, {'message':inbox.message,'from_id':inbox.from_id,
					'date':inbox.date_today,'to_id':inbox.to_id}))
			self.inbox_one2many = inbox_list

			sent_id = self.env['im_chat.message.req'].search([('sent','=',False),('from_id','=', self.env['res.users'].search([('partner_id','=',self.partner_id.id)])[0].id)])
			for sent in sent_id:
				sent_list.append((0, False, {'message':sent.message,
					'date':sent.date_today,'from_id':sent.from_id,'to_id':sent.to_id}))
			self.sent_one2many = sent_list

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=80):
		if args is None:
			args = []
		if operator in expression.NEGATIVE_TERM_OPERATORS:
			domain = [('nick_name', operator, name), ('name', operator, name)]
		else:
			domain = ['|', ('nick_name', operator, name), ('name', operator, name)]
		ids = self.search(cr, user, expression.AND([domain, args]), limit=limit, context=context)
		return self.name_get(cr, user, ids, context=context)
 
	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		if isinstance(ids, (int, long)):
					ids = [ids]
		reads = self.read(cr, uid, ids, ['name', 'nick_name'], context=context)
		res = []
		for record in reads:
			name = record['name']
			if record['nick_name']:
				name = name + ' - ' + record['nick_name']
			res.append((record['id'], name))
		return res


	def _needaction_domain_get(self, cr, uid, context=None):
		return False


class ProjectInbox(models.Model):
	_name = 'project.customer.inbox'

	date = fields.Datetime('Date')
	project_id = fields.Many2one('project.project')
	reply = fields.Text('Reply')
	message = fields.Text('Message')
	from_id = fields.Many2one('res.users','From')
	to_id = fields.Many2one('res.users','To')


class ProjectInbox(models.Model):
	_name = 'project.customer.sent'

	project_sent_id = fields.Many2one('project.project')
	date = fields.Datetime('Date')
	message = fields.Text('Message')
	reply = fields.Text('Reply')
	from_id = fields.Many2one('res.users','From')
	to_id = fields.Many2one('res.users','To')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    designation_id = fields.Many2one('res.groups',string="Designation")
    manager_id = fields.Many2one('hr.employee',string="Manager",domain=[('status1','=','active')])
    parent_id = fields.Many2one('hr.employee',string="Head",domain=[('status1','=','active')])

    # seq_no = fields.Integer(string="Sequence",related='designation_id.sequence')




