from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
import datetime
from datetime import date,datetime
import dateutil.parser
from datetime import timedelta
from openerp.osv import expression

AVAILABLE_PRIORITIES = [
	('0', 'Very Low'),
	('1', 'Low'),
	('2', 'Normal'),
	('3', 'High'),
	('4', 'Very High'),
	('5', 'Excellent')
]

AVAILABLE_PRIORITIES_THREE = [
	('0', 'Very Low'),
	('1', 'Low'),
	('2', 'Normal'),
	('3', 'High'),
]


class TaskWizard(models.Model):
	_name = 'task.wizard'


	# @api.onchange('assigned')
	# def onchange_user_id_pro(self):
	# 	print 'dfffff=====================', self.env.context
	# 	ids = []
	# 	record = False
	# 	if self.env.context.get('default_project_id'):
	# 		record = self.env['project.project'].sudo().browse(self.env.context.get('default_project_id'))
	# 	if record:
	# 		for item in record.members:
	# 			ids.append(item.id)
	# 		return {'domain': {'assigned': [('id', 'in', ids)]}}


	assigned = fields.Many2one('res.users','Assigned To')

	@api.multi
	def task_confirm(self):
		self = self.sudo()
		direct_task = True
		if self.env.context.get('default_project_id'):
			direct_task = False

		return {
			'name': 'Task Creation',
			'view_type': 'form',
			'view_mode': 'calendar,tree,form',
			'res_model': 'event.event',
			'domain': ['|',('project_manager','=',self.assigned.id),('user_id', '=', self.assigned.id)] if self.assigned.id else [],
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {'default_user_id':self.assigned.id,'default_direct_task':direct_task,'default_assigned':[(6, 0, [self.assigned.id])],'default_project_id':self.env.context.get('default_project_id'),'default_wd_id':self.env.context.get('default_wd_id'),'default_activity':self.env.context.get('default_activity'),'default_site_visit':self.env.context.get('default_site_visit')}
		}

class TaskWizardLine(models.Model):
	_name = 'task.wizard.line'

	@api.onchange('assigned')
	def onchange_assigned(self):
		users = []
		user = self.env['res.users'].search([])
		for usr in user:
			if usr.employee_id.id:
				users.append(usr.id)
		return {'domain': {'assigned': [('id', 'in', users)]}}

	assigned = fields.Many2many('res.users',string='Assigned To')
	task_type = fields.Many2one('event.type', 'Type')
	name = fields.Char('Task')
	date_begin = fields.Datetime('Start Time')
	report_time = fields.Datetime('Reporting Time')
	date_end = fields.Datetime('End Time')
	remarks = fields.Text('Remarks')
	project_id = fields.Many2one('project.project', 'Project')
	manager_id = fields.Many2one('res.users', 'Project Manager', related="project_id.user_id")
	company_id = fields.Many2one('res.company', 'Branch', related="project_id.company_id")
	customer_id = fields.Many2one('res.partner', 'Customer', related="project_id.partner_id")
	direct_task = fields.Boolean('Direct Task', default=True)

	@api.model
	def create(self, vals):
		date_date = datetime.strptime(vals['date_begin'], '%Y-%m-%d %H:%M:%S').date()
		emplyees = ""
		for i in vals['assigned'][0][2]:
			usr = self.env['res.users'].browse(i)
			if usr:
				emp = self.env['hr.holidays'].search([('employee_id', '=', usr.employee_id.id), ('state', '=', 'validate')])
				if emp:
					for j in emp:
						date_from = datetime.strptime(j.date_from, '%Y-%m-%d %H:%M:%S').date()
						date_to = datetime.strptime(j.date_to, '%Y-%m-%d %H:%M:%S').date()
						if date_from <= date_date <= date_to:
							emplyees += j.employee_id.name+","
		if emplyees:
			raise ValidationError(str(emplyees) + " have approved leave on that date")
		else:
			res = super(TaskWizardLine, self).create(vals)
			return res

	@api.multi
	def button_save_new(self):
		return{
			'type': 'ir.actions.act_window',
			'name': _('Add Task'),
			'res_model': 'task.wizard',
			'view_type': 'form',
			'view_mode': 'form',
			# 'view_id': view_id,
			'target': 'new',
			'context': {'default_project_id':self.project_id.id,
						'default_company_id':self.company_id.id,
						'default_manager_id':self.manager_id.id,
						'default_customer_id':self.customer_id.id,
						}
		}

	@api.multi
	def button_save(self):
		print "Save"

class DayAbstractWizard(models.Model):
	_name = 'day.abstract.wizard'

	date = fields.Date('Date',  default=datetime.now().date())


	@api.multi
	def action_continue(self):
		tree_id = self.env.ref('hiworth_project_management.event_daily_task_tree').id
		form_id = self.env.ref('hiworth_project_management.event_daily_tasks_form').id
		events = self.env['event.event'].search([])
		start_dt = datetime.strptime(self.date, "%Y-%m-%d")
		start_dt = datetime.strftime(start_dt, "%Y-%m-%d %H:%M:%S")
		start_dt = datetime.strptime(start_dt, "%Y-%m-%d %H:%M:%S")
		h=start_dt.hour+18
		m=start_dt.minute-29
		end_dt = start_dt + timedelta(hours=h,minutes=m)
		from_dt = end_dt - timedelta(days=1)
		end_dt = datetime.strftime(end_dt, "%Y-%m-%d %H:%M:%S")
		from_dt = datetime.strftime(from_dt, "%Y-%m-%d %H:%M:%S")
		return{
			'name': 'Day Abstract',
			'view_type':'form',
			'view_mode':'tree,form',
			'type': 'ir.actions.act_window',
			'res_model': 'event.event',
			'domain': [('date_end','>=',from_dt),('date_end','<',end_dt),('state','in',('draft','initial'))],
			'views' : [(tree_id,'tree'),(form_id, 'form')],
			'view_id': False,
			'target': 'current',
			# 'context': {},
		}


class EvaluateRatingLine(models.Model):
	_name = 'evaluate.rating.line'

	line_id = fields.Many2one('evaluate.rating')
	report_rate = fields.Many2one('evaluate.rating')
	proceed_rate = fields.Many2one('evaluate.rating')	
	name = fields.Char()
	priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority', select=True)
	priority1 = fields.Selection(AVAILABLE_PRIORITIES_THREE, string='Priority', select=True)



class EvaluateRating(models.Model):
	_name = 'evaluate.rating'

	@api.multi
	def return_rating(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_evaluate_form')
		view_id = view_ref[1] if view_ref else False
		res = {
			'type': 'ir.actions.act_window',
			'name': _('Evaluate'),
			'res_model': 'evaluate.rating',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': view_id,
			'target': 'new',
			'context': {'default_rec':self.rec.id,'default_rate_to':self.rec.user_id.id if self.env.user.id != 1 else self.rec.project_manager.id,'default_flag':'flag','default_report_rate':False}
		}

		return res

	@api.multi
	def proceed_rating(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_evaluate_form')
		view_id = view_ref[1] if view_ref else False
		res = {
			'type': 'ir.actions.act_window',
			'name': _('Evaluate'),
			'res_model': 'evaluate.rating',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': view_id,
			'target': 'new',
			'context': {'default_rec':self.rec.id,'default_rate_to':self.rec.user_id.id if self.env.user.id != 1 else self.rec.project_manager.id,'default_flag':'draft','default_report_rate':False}
		}
		return res


	@api.multi
	@api.depends('rating_line','rating_line1','flag','report_rate')
	def _get_task_rating(self):
		count = 0
		rate = 0
		if self.report_rate == True:
			for lines in self.rating_line:
					count += 1
					rate += float(lines.priority)		
		else:
			for lines in self.rating_line1:
				count += 1
				rate += float(lines.priority)		

		if count != 0:
			self.task_rating = float(rate/count)


	rec = fields.Many2one('event.event', string="Task")
	rating_line = fields.One2many('evaluate.rating.line','line_id')
	rating_line1 = fields.One2many('evaluate.rating.line','report_rate')
	rating_line2 = fields.One2many('evaluate.rating.line','proceed_rate')
	report_rate = fields.Boolean(default=True)
	task_rating = fields.Float(string='Rating', compute="_get_task_rating")
	rate_to = fields.Many2one('res.users','Rate To')
	flag = fields.Selection([('draft','Draft'),('flag','Flag')],default='draft')
	reason = fields.Text('Reason')

	@api.model
	def default_get(self, default_fields):
		vals = super(EvaluateRating, self).default_get(default_fields)
		domain = []
		if 'rec' not in default_fields:
			event = self.env.context.get('active_id')
			domain.append(('id','=',event))
		else:
			domain.append(('id','=',vals['rec']))
		task = self.env['event.event'].search(domain)
		list=[]
		list1 = []
		for line in task.type.eval_line1:
			# if line.id in [1,2,3,4,5]:
			list.append({'name':line.name})
		for lines in task.type.eval_line2:
			# if lines.id in [1,2,3,4,5]:
			list1.append({'name':lines.name})
		vals['rating_line'] = list
		vals['rating_line1'] = list1
		vals['rating_line2'] = list1
		return vals



	@api.multi
	def rate_staff(self):
		# if self.report_rate == False and self.flag == 'flag':
		# 	self.rec.man_rate = True
		# 	self.rec.priority_man = self.task_rating
		# 	self.rec.state = 'evaluated'
		# 	view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'event_all_tasks_form')
		# 	view_id = view_ref[1] if view_ref else False
		# 	res = {
		# 		'type': 'ir.actions.act_window',
		# 		'name': _('Task'),
		# 		'res_model': 'event.event',
		# 		'view_type': 'form',
		# 		'view_mode': 'form',
		# 		'view_id': view_id,
		# 		'target': 'current',
		# 		'context': {'default_name':self.rec.name,
		# 					'default_project_id':self.rec.project_id.id,
		# 					'default_company_id':self.rec.project_id.company_id.id,
		# 					'default_project_manager':self.rec.project_manager.id,
		# 					'default_reviewer_id':self.rec.reviewer_id.id,
		# 					'default_civil_contractor':self.rec.civil_contractor.id,
		# 					'default_current_user':self.env.user.id,
		# 					'default_is_silent':self.rec.is_silent,
		# 					'default_user_id':self.rec.project_manager.id,
		# 					'default_type':self.rec.type.id,
		# 					'default_reason_for_return':True,
		# 					'default_reason':self.reason,
		# 					}
		# 	}

		# 	return res

		# else:

		# 	if self.env.user.id == 1:
		# 		if self.rec.man_rate == False:
		# 			self.rec.man_rate = True
		# 			self.rec.state = 'evaluated'
		# 			self.rec.priority_man = self.task_rating
		# 		else:
		# 			raise except_orm(_('Warning'),
		# 							 _('Already Rated'))
		# 	else:
		# 		if self.rec.emp_rate == False:
		# 			self.rec.emp_rate = True
		# 			self.rec.priority = self.task_rating
		# 		else:
		# 			raise except_orm(_('Warning'),
		# 							 _('Already Rated'))


		#####################################################	
		if self.rec.emp_rate == True and self.rec.man_rate == False:			
			self.rec.man_rate = True
			self.rec.state = 'evaluated'
			self.rec.priority_man = self.task_rating
			if self.report_rate == False and self.flag == 'flag':
				view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'event_all_tasks_form')
				view_id = view_ref[1] if view_ref else False
				res = {
						'type': 'ir.actions.act_window',
						'name': _('Task'),
						'res_model': 'event.event',
						'view_type': 'form',
						'view_mode': 'form',
						'view_id': view_id,
						'target': 'current',
						'context': {'default_name':self.rec.name,
									'default_project_id':self.rec.project_id.id,
									'default_company_id':self.rec.project_id.company_id.id,
									'default_project_manager':self.rec.project_manager.id,
									'default_reviewer_id':self.rec.reviewer_id.id,
									'default_civil_contractor':self.rec.civil_contractor.id,
									'default_current_user':self.env.user.id,
									'default_is_silent':self.rec.is_silent,
									'default_user_id':self.rec.project_manager.id,
									'default_type':self.rec.type.id,
									'default_reason_for_return':True,
									'default_reason':self.reason,
									}
					}

				return res

		if self.rec.emp_rate == False and self.rec.man_rate == False:
			self.rec.emp_rate = True
			self.rec.priority = self.task_rating		

		######################################################

		rec = self.env['task.rate.line'].create({'date':fields.Datetime.now(),
												 'task_id':self.rec.id,
												 'average':self.task_rating,
												 'rate_id':self.rate_to.employee_id.id})
		user_ids = []
		for g in self.env['res.groups'].search(
				[('sequence', '<', self.env.user.employee_id.user_category.sequence), ('sequence', '>', 0)]):
			for user in g.users:
				if user.id not in user_ids:
					user_ids.append(user.id)
		for u in user_ids:
			self.env['popup.notifications'].sudo().create({
				'name': u,
				'status': 'draft',
				'message': " Task name " + self.rec.name + " is rated by "+self.env.user.name})


class EventEvent(models.Model):
	_inherit = 'event.event'
	_order = 'date_begin'


	@api.model
	def default_get(self, default_fields):
		vals = super(EventEvent, self).default_get(default_fields)
		if vals.get('project_id'):
			project = self.env['project.project'].browse(vals.get('project_id'))
			vals['project_manager'] = project.user_id.id
			vals['civil_contractor'] = project.partner_id.id
		if vals.get('date_end'):
			# self.date = dateutil.parser.parse(self.date_end).date() 
			date_end = fields.Datetime.from_string(vals.get('date_end'))
			vals['report_time'] = fields.Datetime.to_string(date_end - timedelta(minutes=60))
		if vals.get('wd_id'):
			wd = self.env['job.assignment'].browse(vals.get('wd_id'))
			vals['civil_contractor'] = wd.user_id.id
		return vals


	@api.onchange('date_end','date_begin')
	def onchange_date_end(self):
		# print 'context==================', self.env.context, self.user_id,self.user_ids
		if self.date_end:
			if self.date_end <self.date_begin:
				raise except_orm(_('Warning'),
								 _('please select an end date greater than start date'))
			else:

				self.date = dateutil.parser.parse(self.date_end).date()
				date_end = fields.Datetime.from_string(self.date_end)
				self.report_time = fields.Datetime.to_string(date_end - timedelta(minutes=60))
				events = self.env['event.event'].search([('user_id','=',self.user_id.id),'|','&',('date_begin','>=',self.date_begin),('date_begin','<=',self.date_end),'&',('date_end','>=',self.date_begin),('date_end','<=',self.date_end)])
				if events:
					raise except_orm(_('Warning'),
									 _('Already some task is assigned for this time slot. Do you want to continue...!!!'))


	@api.onchange('user_id','user_ids','project_id')
	def onchange_user_id_pro(self):
		ids = []
		record = False
		if self.env.context.get('default_project_id'):
			record = self.env['project.project'].sudo().browse(self.env.context.get('default_project_id'))
		if self.project_id:
			self.project_manager = self.project_id.user_id.id
			self.civil_contractor = self.project_id.partner_id.id
			if self.env.context.get('default_project_id'):
				record = self.env['project.project'].sudo().search([('id','=',self.env.context.get('default_project_id'))])
			else:
				record = self.env['project.project'].sudo().search([('id','=',self.project_id.id)])
		if record:
			for item in record.members:
				ids.append(item.id)
		if self.activity == False and self.site_visit == False:
			return {'domain': {'user_id': [('id', 'in', ids)], 'user_ids': [('id', 'in', ids)]}}

	@api.one
	def button_draft(self):
		self.state = 'initial'
		self.status = 'initial'

	@api.one
	def complete_task(self):
		self.state = 'completed'
		user_ids = []
		user_ids.append(self.current_user.id)
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
				'message':"The Task ("+str(self.name)+str(" ) is completed"),
				'status':'draft',
			})
		return


	@api.multi
	def finish_task(self):
		self.state = 'completed'
		self.status = 'completed'
		user_ids = []
		if not self.type:
			self.type = self.parent_id.type.id or False
		if not self.project_manager:
			self.project_manager = self.parent_id.project_manager.id or False
		if not self.civil_contractor:
			self.civil_contractor = self.parent_id.civil_contractor.id or False
		self.completion_time = datetime.now()
		for g in self.env['res.groups'].search([('sequence', '<', self.user_id.employee_id.user_category.sequence),('sequence', '>', 0)]):
			for user in g.users:
				if user.id not in user_ids:
					user_ids.append(user.id)
		for u in user_ids:
			self.env['popup.notifications'].sudo().create({
				'name': u,
				'status': 'draft',
				'message': " Task name "+ str(self.name) +" is completed by "+str(self.user_id.name)})

	@api.multi
	@api.depends('name','project_id','wd_id')
	def compute_project_name(self):
		for rec in self:
			if rec.project_id:
				partner_name = ''
				if rec.project_id.partner_id:
					partner_name = rec.project_id.partner_id.name
				rec.project_name = rec.project_id.name + ' - '+ partner_name
			if rec.wd_id:
				user_name = ''
				if rec.wd_id.user_id:
					user_name = rec.wd_id.user_id.name
				rec.project_name = rec.wd_id.name+' - '+ user_name

	def change_colore_on_kanban(self):
		"""    this method is used to chenge color index    base on fee status    ----------------------------------------    :return: index of color for kanban view    """
		for record in self:
			color = 0
			if record.state == 'initial':
				color = 2
			elif record.state == 'completed':
				color = 6
			elif record.state == 'evaluated':
				color = 5
			record.color = color


	color = fields.Integer('Color Index', compute="change_colore_on_kanban")
	number = fields.Char(default='/',readonly=True)
	is_silent = fields.Boolean('Is Silent')
	name = fields.Char(string='Task Name', translate=False, required=True)
	man_rate = fields.Boolean(default=False)
	emp_rate = fields.Boolean(default=False)
	event_project = fields.Many2one('project.project',store=True)
	project_id = fields.Many2one('project.project',string="Project Name")
	company_id = fields.Many2one('res.company', string='Branch', related=False)
	report = fields.Text('Report')
	civil_contractor = fields.Many2one('res.partner','Customer')
	reviewer_id = fields.Many2one('res.users','Reviewer')
	project_manager = fields.Many2one('res.users','Project Manager')
	report_time = fields.Datetime('Reporting Time',required=True)

	status = fields.Selection([('initial','Not Completed'),('completed','Completed')],default="initial",string="Status")
	remarks = fields.Text('Remarks')
	status1 = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	date = fields.Date('Date')
	duration=fields.Float('duration')
	current_user = fields.Many2one('res.users',string="User")
	priority = fields.Float(readonly=True)
	priority_man = fields.Float(readonly=True)
	update_sel = fields.Selection([('not','Not'),('bw','Bw'),('updated','Updated')],default='not')
	update = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	state = fields.Selection([
		('draft', 'Draft'),
		('cancel', 'Cancelled'),
		('confirm', 'Confirmed'),
		('done', 'Done'),
		('initial','Ongoing'),
		('completed','Completed'),
		('evaluated', 'Evaluated')
	], string='Status', default='initial', readonly=True, required=True, copy=False)
	date_begin = fields.Datetime(string='Start Date', required=True,
								 readonly=True, states={'initial': [('readonly', False)]})
	date_end = fields.Datetime(string='End Date', required=True,
							   readonly=True, states={'initial': [('readonly', False)]})
	completion_time = fields.Datetime(string='Completion Date',
									  readonly=True)
	activity = fields.Boolean(default=False)
	site_visit = fields.Boolean(default=False)
	work_stage_site = fields.Char('Work Stage')
	update_man = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	reason_for_return = fields.Boolean(default=False)
	reason = fields.Text('Reason',readonly=True)
	wd_id = fields.Many2one('job.assignment', 'Work Description')
	pj_id = fields.Many2one('project.project', 'Project')
	location = fields.Many2one('stock.location','Location Of Site',domain=[('usage','=','internal')])
	re_task = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	popup_id = fields.Many2one('popup.notifications', 'Popup')
	user_id = fields.Many2one('res.users', string='Responsible User',
							  default=False,
							  readonly=False, states={'done': [('readonly', True)]})
	report_id = fields.Many2one('work.report', 'Report')
	user_ids = fields.Many2many('res.users','event_user_rel', 'event_id','user_id', 'Assigned To')
	copy = fields.Boolean('Is Copy', default=False)
	parent_id = fields.Many2one('event.event', 'Parent')
	project_name = fields.Char(compute='compute_project_name', string="Project")

	@api.one
	def button_confirm1(self):
		self.state = 'initial'

	@api.multi
	def button_evaluate(self):
		if self.emp_rate == True:
			view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_evaluate_form_proceed')
			view_id = view_ref[1] if view_ref else False
			res = {
				'type': 'ir.actions.act_window',
				'name': _(''),
				'res_model': 'evaluate.rating',
				'view_type': 'form',
				'view_mode': 'form',
				'view_id': view_id,
				'target': 'new',
				'context': {'default_rec':self.id,}
			}

			return res
		else:
			flag = 0
			if self.user_id.id != self.env.user.id:
				if self.emp_rate == True:
					flag = 1
			view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_first_evaluate_form')
			view_id = view_ref[1] if view_ref else False
			res = {
				'type': 'ir.actions.act_window',
				'name': _('Evaluate'),
				'res_model': 'evaluate.rating',
				'view_type': 'form',
				'view_mode': 'form',
				'view_id': view_id,
				'target': 'new',
				'context': {'default_rec':self.id,'default_rate_to':self.user_id.id if self.env.user.id != 1 else self.project_manager.id,'default_flag':'flag' if flag == 1 else 'draft'}
			}

			return res

	@api.multi
	def send_work_report(self):
		gm = self.env.ref("hiworth_project_management.group_general_manager")
		user_ids = []
		for user in gm.users:
			user_ids.append(user.id)
		manager_id = self.project_id and self.project_id.user_id or False
		if manager_id:
			user_ids.append(manager_id.id)
		for user in user_ids:
			self.env['popup.notifications'].sudo().create({
													'name':user,
													'message':"You have daily report to Approve from "+str(self.user_id.name),
													'status':'draft',
					})
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_work_report_staff_form')
		view_id = view_ref[1] if view_ref else False
		# print 'branch_id=========================', self.user_id.company_id.i
		res = {
			'type': 'ir.actions.act_window',
			'name': _('Daily Report'),
			'res_model': 'work.report',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': view_id,
			'target': 'current',
			'context': {'default_req_end':True if self.state == 'completed' else False,'default_report':self.report,'default_project':self.project_id.id,'default_task_id':self.id,'default_date_end':self.date_end,'default_branch_id':self.user_id.company_id.id}
		}

		return res


	_defaults = {

		'reviewer_id': lambda obj, cr, uid, ctx=None: 1,
		'current_user': lambda obj, cr, uid, ctx=None: uid,

	}



	@api.model
	def create(self, vals):

		then = datetime.strptime(vals.get('date_begin'),'%Y-%m-%d %H:%M:%S').date()
		if then<datetime.now().date():
			raise except_orm(_('Warning'),
							 _('You Can not create task on this start date..!!'))
		if vals.get('user_ids'):
			if vals.get('user_ids')[0][2]:
				vals['user_id'] = vals.get('user_ids')[0][2][0]
		# print 'vals===================', vals
		result = super(EventEvent, self).create(vals)
		if result.number == '/':
			result.number = self.env['ir.sequence'].next_by_code('event.event') or '/'
		activity = False
		site_visit = False
		if result.site_visit == True:
			site_visit = True
		if result.activity == True:
			activity = True
			popup = self.env['popup.notifications'].create({
				'name':result.user_id.id,
				'message':"You have a Activity ("+str(result.name)+str(" )"),
				'status':'draft',
			})
		else:
			popup = self.env['popup.notifications'].create({
				'name':result.user_id.id,
				'message':"You have a Activity ("+str(result.name)+str(" )"),
				'status':'draft',
			})
		if popup:
			result.popup_id = popup.id
		if result.activity == True or result.site_visit == True:
			result.company_id = result.wd_id.branch_name.id
		else:
			result.company_id = result.project_id.company_id.id
		temp = False
		user_list = [i.id for i in result.user_ids]
		print 'test=====================1'
		for user in result.user_ids:
			if temp == False:
				result.user_id = user.id
				temp = True
			if user.id != result.user_id.id:
				print 'test=====================2'
				values = {
					'wd_id': result.wd_id.id,
					'name': result.name,
					'current_user': result.current_user.id,
					'user_id': user.id,
					'remarks': result.remarks,
					'date_begin': result.date_begin,
					'report_time': result.report_time,
					'date_end': result.date_end,
					'activity': activity,
					'site_visit': site_visit,
					'user_ids': [(6, 0, user_list)],
					# 'copy': True,
					'parent_id': result.id,
					'location': result.location.id,
					'project_id': result.project_id.id,
				}
				copy = super(EventEvent, self).create(values)
				print 'copy==================================',copy
				# super(EventEvent, self).create(vals)
				if copy.activity == True:
					popup = self.env['popup.notifications'].create({
						'name':copy.user_id.id,
						'message':"You have a Activity ("+str(copy.name)+str(" )"),
						'status':'draft',
					})
				else:
					popup = self.env['popup.notifications'].create({
						'name':copy.user_id.id,
						'message':"You have a Activity ("+str(copy.name)+str(" )"),
						'status':'draft',
					})
				if popup:
					copy.popup_id = popup.id
				if copy.activity == True or copy.site_visit == True:
					copy.company_id = copy.wd_id.branch_name.id
				else:
					copy.company_id = copy.project_id.company_id.id
		print 'user_ids========================', result.user_ids
		return result




	@api.multi
	def write(self, vals):
		if vals.get('date_begin'):
			then = datetime.strptime(vals.get('date_begin'),'%Y-%m-%d %H:%M:%S').date()
			if then<datetime.now().date():
				print '=================================test'
				raise except_orm(_('Warning'),
								 _('You Can not create task on this start date..!!'))
		if self.popup_id:
			if vals.get('name'):
				self.popup_id.message = "You have a Task ("+str(vals.get('name'))+str(" )")
			if vals.get('user_id'):
				self.popup_id.name = vals.get('user_id')
		if (vals.get('name') or vals.get('user_id')) and not self.popup_id:
			popup = self.env['popup.notifications'].create({
				'name':vals.get('user_id') if vals.get('user_id') else self.user_id.id,
				'message':"You have a Task ("+str(vals.get('name') if vals.get('name') else self.name)+str(" )"),
				'status':'draft',
			})
			if popup:
				self.popup_id = popup.id
		events = self.env['event.event'].search([('parent_id','=',self.id)])
		for event in events:
			if vals.get('name') and not vals.get('user_ids'):
				event.name = vals.get('name')
			if vals.get('wd_id') and not vals.get('user_ids'):
				event.wd_id = vals.get('wd_id')
			if vals.get('remarks') and not vals.get('user_ids'):
				event.remarks = vals.get('remarks')
			if vals.get('date_begin') and not vals.get('user_ids'):
				event.date_begin = vals.get('date_begin')
			if vals.get('report_time') and not vals.get('user_ids'):
				event.report_time = vals.get('report_time')
			if vals.get('date_end') and not vals.get('user_ids'):
				event.date_end = vals.get('date_end')
			if vals.get('location') and not vals.get('user_ids'):
				event.location = vals.get('location')
		if vals.get('user_ids'):
			raise except_orm(_('Warning'),
							 _('If you want to change users then delete this record and create new one.!!'))

		result = super(EventEvent, self).write(vals)


		if vals.get('status') and self.env.uid != 1:
			if vals.get('status') == 'completed':
				self.update_sel = 'bw'


		return result


	@api.multi
	@api.depends('name', 'date_begin', 'date_end')
	def name_get(self):
		result = []
		for event in self:
			date_begin = fields.Datetime.from_string(event.date_begin)
			date_end = fields.Datetime.from_string(event.date_end)
			dates = [fields.Date.to_string(fields.Datetime.context_timestamp(event, dt)) for dt in [date_begin, date_end] if dt]
			dates = sorted(set(dates))
			result.append((event.id, '%s' % (event.name)))
		return result

	@api.multi
	def unlink(self):
		for record in self:
			events = self.env['event.event'].search([('parent_id','=',record.id)])
			for event in events:
				event.popup_id.unlink()
				event.unlink()
			record.popup_id.unlink()
		return super(EventEvent, self).unlink()

class ProjectCategory(models.Model):

	_rec_name = 'name'
	_name = 'project.category'

	name = fields.Char('Name', required=True)

class Project_Co_Applicants(models.Model):

	_rec_name = 'name'
	_name = 'project.co.applicants'

	project_id = fields.Many2one('project.project')
	name = fields.Char('Name')

class ProjectProject(models.Model):
	_inherit = 'project.project'
	_order = 'start_date desc'

	year = fields.Char()
	co_applicants = fields.One2many('project.co.applicants', 'project_id')
	task_wizard_ids = fields.One2many('task.wizard.line','project_id')
	sup_project_description = fields.Char()


	def onchange_partner_id(self, cr, uid, ids, part=False, context=None):
		res = super(ProjectProject, self).onchange_partner_id(cr, uid, ids, part, context)
		cr = cr
		uid = uid
		context=context
		user_obj = self.pool.get('res.users')
		user_id = user_obj.search(cr,uid,[('partner_id','=',part)],context)
		res['value'].update({'user_part_id':user_id and user_id[0] and []})
		return  res

	@api.model
	def create(self, vals):
		if vals['start_date']:
			vals['year'] = vals['start_date'].split('-')[0]
		result = super(ProjectProject, self).create(vals)
		if result['partner_id']:
			rec = self.env['res.users'].sudo().search([('partner_id','=',result['partner_id'].id)])
			if rec:
				result['customer_email'] = rec.login

		if result['name'] == '/':
			seq = self.env['ir.sequence'].next_by_code('project.project')
			result['name'] = str('PBA')+str('/')+str(result['company_id'].name)+str('/')+str(result['project_category'].name)+str('/')+seq[:3]+str('/')+seq[-4:]
		job_assign = self.env['job.assignment']
		dob = ''
		if result['partner_id'].years:
			dob = datetime.strptime(str(result['partner_id'].years)+"-"+str(result['partner_id'].dobm)+"-"+str(result['partner_id'].days), "%Y-%B-%d").strftime("%Y-%m-%d")
		rec = job_assign.sudo().create({
			'name': result['name'] or False,
			'location': vals['location_id'] or False,
			'user_id': vals['partner_id'] or False,
			'no_stories': vals['no_story'] or False,
			'area_limit': vals['area'] or False,
			'dob':dob,
			'bldng_direction': vals['face_direction'] or False,
			'manager': vals['user_id'] or False,
			'latitude': vals['latitude'] or False,
			'longitude': vals['longitude'] or False,
			'project_category': vals['project_category'] or False,
			'branch': vals['company_id'] or False,
		})
		result['job_assignment'] = rec.id
		return result


	@api.multi
	def write(self, vals):
		manager = self.user_id.id
		if vals.get('user_id'):
			if manager == self.env.user.id:
				raise except_orm(_('Warning'),
								 _('You Can not change the manager..!!'))
		if vals.get('start_date'):
			vals['year'] = vals.get('start_date').split('-')[0]
		result = super(ProjectProject, self).write(vals)
		if vals.get('partner_id'):
			rec = self.env['res.users'].search([('partner_id','=',vals.get('partner_id'))])
			if rec:
				self.customer_email = rec.login

		return result

	def set_open(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'open','status_pro':'ongoing'}, context=context)

	def set_done(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'close','status_pro':'completed'}, context=context)

	def set_pending(self, cr, uid, ids, context=None):
		return self.write(cr, uid, ids, {'state': 'pending','status_pro':'pending'}, context=context)

	@api.multi
	def set_customer_user(self):
		for rec in self.search([]):
			user_obj = self.env['res.users']
			user_id = user_obj.search([('partner_id','=',rec.partner_id.id)])
			rec.user_part_id = user_id.id
		
	
	@api.multi
	def create_activity(self):
		return {
			'type': 'ir.actions.act_window',
			'name': _('Add Activity'),
			'res_model': 'task.wizard',
			'view_type': 'form',
			'view_mode': 'form',
			# 'view_id': view_id,
			'target': 'new',
			'context': {'default_pj_id': self.id, 'default_activity': True}
		}

	@api.multi
	def create_work_site(self):
		return {
			'type': 'ir.actions.act_window',
			'name': _('Add Activity'),
			'res_model': 'task.wizard',
			'view_type': 'form',
			'view_mode': 'form',
			# 'view_id': view_id,
			'target': 'new',
			'context': {'default_pj_id': self.id, 'default_site_visit': True}
		}

	@api.multi
	def reopen_project(self):
		project_count = self.project_count
		project_count += 1
		members = []
		for m in self.members:
			members.append((4, [m.id]))
		self.project_count = project_count
		self.env['project.project'].create(
			{
				'name':self.name[:-4]+str(project_count)+str('/')+self.name[-4:],
				'location_id':self.location_id.id,
				'parent_project':self.id,
				'is_subproject':True,
				'user_id':self.user_id.id,
				'partner_id':self.partner_id.id,
				'start_date':self.start_date,
				'date_end':self.date_end,
				'project_category':self.project_category.id,
				'company_id':self.company_id.id,
				'face_direction':self.face_direction.id,
				'area':self.area,
				'plote_data':self.plote_data,
				'building_no':self.building_no,
				'latitude':self.latitude,
				'longitude':self.longitude,
				'north':self.north,
				'east':self.east,
				'west':self.west,
				'south':self.south,
				'district':self.district,
				'taluk':self.taluk,
				'village':self.village,
				'no_story':self.no_story,
				'building_nature':self.building_nature,
				'permit_authority':self.permit_authority,
				'permit_no':self.permit_no,
				'permit_from':self.permit_from,
				'permit_to':self.permit_to,
				'inv_button':True,
				'members':members
			})

	@api.multi
	def name_get(self):
		result = []
		for record in self:
			if record.partner_id.nick_name:
				result.append((record.id,u"%s (%s)" % (record.name, record.partner_id.nick_name)))
			else:
				result.append((record.id,u"%s" % (record.name)))
		return result


	@api.onchange('members')
	def onchange_members(self):
		if self.company_id:
			ids = []
			record = self.env['res.users'].sudo().search([('partner_id.is_cus','=',False), ('active', '=', True)])
			if record:
				for item in record:
					ids.append(item.id)
				return {'domain': {'members': [('id', 'in', ids)]}}

	@api.multi
	def add_image(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_ir_attachment_form_view')
		view_id = view_ref[1] if view_ref else False
		res = {
			'type': 'ir.actions.act_window',
			'name': _('Add Image'),
			'res_model': 'ir.attachment',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': view_id,
			'target': 'new',
			'context': {'default_project_image':self.id, 'default_gallery': 0}
		}

		return res

	job_assignment = fields.Many2one('job.assignment', 'Work Description')
	contact1 = fields.Char('Contact number of Customer',related="partner_id.phone")
	contact2 = fields.Char('Contact',related="partner_id.mobile")
	event = fields.One2many('event.event','project_id',string='Tasks')
	parent_project = fields.Many2one('project.project',string='Parent Project')
	project_count = fields.Integer(default=0)
	no_story = fields.Char('No Of Stories')
	inv_button = fields.Boolean(default=False)
	work_report_man = fields.Many2one('res.users')
	work_reports = fields.One2many('work.report','project',string='Approved Work Reports')
	site_image = fields.Many2many('ir.attachment','project_img_rel', 'project_id','attachment_id')
	keywords = fields.Many2many('keywords.tags','keyword_tags_rel','keyword','tags',string="keywords")
	face_direction = fields.Many2one('facing.direction',string="Facing Direction")
	status_pro = fields.Selection([('ongoing','On Going'),('pending','Pending'),('completed','Completed')],default='ongoing')
	project_category = fields.Many2one('project.category','Project Category',required=True)
	drawing_sheet = fields.One2many('ir.attachment','drawing_id')
	customer_email = fields.Char('Email',readonly=True)
	customer_nick_name = fields.Char('Nick Name',related="partner_id.nick_name")
	customer = fields.Boolean('Customer',related='partner_id.customer')    
	house_name = fields.Char('House Name',related="partner_id.house_name")
	street = fields.Char('Street',related="partner_id.street")
	street2 = fields.Char('Street2',related="partner_id.street2")
	city = fields.Char('City',related="partner_id.city")
	state_id = fields.Many2one('res.country.state','State',related="partner_id.state_id")
	country_id = fields.Many2one('res.country','Country',related="partner_id.country_id")
	activities_line = fields.One2many('event.event', 'pj_id', domain=[('copy', '=', False)])
	my_remarks = fields.Text('Remarks')
	initial_meeting = fields.Date('Expected date of initial meeting')
	final_meeting = fields.Date('Date of Finalisation')
	issuing_submission = fields.Date('Date of issuing Submission File')
	issuing_working = fields.Date('Date of issuing Working File')
	remark1 = fields.Char('Remarks')
	remark2 = fields.Char('Remarks')
	revisions = fields.One2many('rivision.remark', 'pj_id')
	site_visit_line = fields.One2many('event.event', 'pj_id')
	inactive_project = fields.Boolean('Inactive',default=False)
	is_subproject = fields.Boolean('Is Subproject',default=False)
	user_part_id = fields.Many2one('res.users'," Customer Users")

	@api.onchange('company_id')
	def onchange_company_id(self):
		if self.company_id:
			users = [46,1]
			user = self.env['res.users'].search([])
			for usr in user:
				if self.company_id == usr.employee_id.company_id :
					if (self.pool['res.users'].has_group(self._cr, self._uid, 'project.group_project_manager') or self.pool['res.users'].has_group(self._cr, self._uid, 'hiworth_project_management.group_general_manager'),self.pool['res.users'].has_group(self._cr, self._uid, 'hiworth_project_management.group_general_manager')):
						users.append(usr.id)
			return {'domain':{'user_id':[('id', 'in', users)]}}


			
	@api.multi
	def create_task(self):
		return{
			'type': 'ir.actions.act_window',
			'name': _('Add Task'),
			'res_model': 'task.wizard',
			'view_type': 'form',
			'view_mode': 'form',
			# 'view_id': view_id,
			'target': 'new',
			'context': {'default_project_id':self.id,
						'default_company_id':self.company_id.id,
						'default_manager_id':self.user_id.id,
						'default_customer_id':self.partner_id.id,
						}
		}

	@api.multi
	def confirm_task(self):
		for val in self.task_wizard_ids:
			a = self.env['event.event'].create({
											'name':val.name,
											'project_id':val.project_id.id,
											'project_manager':val.manager_id.id,
											# 'reviewer_id':val.,
											'civil_contractor':val.customer_id.id,
											'remarks':val.remarks,
											'type':val.task_type.id,
											'date_begin':val.date_begin,
											'report_time':val.report_time,
											'date_end':val.date_end,
											'user_ids':[(6, 0, [i.id for i in val.assigned])],
											# 'completion_time':val.,
											})
			if a:
				val.unlink()



class AccountAnalyticAccount(models.Model):
	_inherit = 'account.analytic.account'

	name = fields.Char('Account/Contract Name', default="/",required=False, track_visibility='onchange')

class FacingDirection(models.Model):
	_name = 'facing.direction'

	name = fields.Char('Direction')


class KeywordTags(models.Model):
	_name = 'keywords.tags'

	name = fields.Char('Name')

class ResPartner(models.Model):
	_inherit = 'res.partner'

	def get_country_id_customer(self):
		country = self.env['res.country'].search([('code','=','IN')])
		if country:
			if country[0]:
				return country[0]
	
	
	
	
		


	is_cus = fields.Boolean()
	cus_date = fields.Date('Date',default=fields.Date.today())
	my_remarks = fields.Text('Remarks')
	external_user = fields.Boolean('External User', default=False)
	user = fields.Many2one('res.users', 'Assigned to')
	nick_name = fields.Char('Nick Name')
	dob = fields.Date('DOB')
	dobm = fields.Selection([
		('January','January'),
		('February','February'),
		('March','March'),
		('April','April'),
		('May','May'),
		('June','June'),
		('July','July'),
		('Augest','Augest'),
		('September','September'),
		('October','October'),
		('November','November'),
		('December','December'),
	], string='Month')
	days = fields.Selection([(num, str(num)) for num in range(1,32)], 'Day')
	years = fields.Selection([(num, str(num)) for num in range(1000,2060)], 'Years')
	dobwh = fields.Selection([
		('January','January'),
		('February','February'),
		('March','March'),
		('April','April'),
		('May','May'),
		('June','June'),
		('July','July'),
		('Augest','Augest'),
		('September','September'),
		('October','October'),
		('November','November'),
		('December','December'),
	], string='Month')
	dayswh = fields.Selection([(num, str(num)) for num in range(1,32)], 'Day')
	yearswh = fields.Selection([(num, str(num)) for num in range(1000,2060)], 'Years')

	dobw = fields.Selection([
		('January','January'),
		('February','February'),
		('March','March'),
		('April','April'),
		('May','May'),
		('June','June'),
		('July','July'),
		('Augest','Augest'),
		('September','September'),
		('October','October'),
		('November','November'),
		('December','December'),
	], string='Month')
	daysw = fields.Selection([(num, str(num)) for num in range(1,32)], 'Day')
	yearsw = fields.Selection([(num, str(num)) for num in range(1000,2060)], 'Years')
	occupation = fields.Char('Occupation')
	street1 = fields.Char('Street')
	street3 = fields.Char('Post Office')
	city1 = fields.Char('City')
	state_id1 = fields.Many2one('res.country.state')
	country_id = fields.Many2one('res.country',default=get_country_id_customer)
	country_id1 = fields.Many2one('res.country',default=get_country_id_customer)
	zip1 = fields.Char('Zip')
	wife_hus = fields.Char('Wife/Husband')
	dob_wh = fields.Date('DOB')
	# children = fields.One2many('children.details','children_id')
	mobile_line_new = fields.One2many('mob.details','mob_id')
	wdng_day = fields.Date('Wedding Anniversary Date')
	# remarks = fields.Text('Remarks')
	res_id1 = fields.Integer()
	current_user = fields.Many2one('res.users')
	house_name = fields.Char('House Name')
	house_name2 = fields.Char('House Name')
	wdng_m = fields.Selection([
		('January','January'),
		('February','February'),
		('March','March'),
		('April','April'),
		('May','May'),
		('June','June'),
		('July','July'),
		('Augest','Augest'),
		('September','September'),
		('October','October'),
		('November','November'),
		('December','December'),
	], string='Month')
	wdng_d = fields.Selection([(num, str(num)) for num in range(1,32)], string='Day')
	

	_defaults = {
		'user': lambda obj, cr, uid, ctx=None: uid,
	}

			
	@api.onchange("country_id",'country_id1')
	def onchange_country_id_pro(self):
		if self.country_id or self.country_id1:
			ids = []

			record = self.env['res.country.state'].search([('country_id','=',self.env['res.country'].search([('code','=','IN')])[0].id)])

			if record:
				for item in record:
					ids.append(item.id)
				return {'domain': {'state_id': [('id', 'in', ids)],
								   'state_id1': [('id', 'in', ids)]}}



	@api.multi
	def write(self, vals):
		result = super(ResPartner, self).write(vals)
		if vals.get('email'):
			rec = self.env['res.users'].search([('partner_id','=',self.id)])
			if rec:
				rec.write({'login':vals['email']})
		return result

	@api.model
	def create(self, vals):
		group_id = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_user').id
		group_id_contractor = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_contractor').id

		user_id = False
		result = super(ResPartner, self).create(vals)
		companies= []
		if result.company_id:
			companies.append(result.company_id.id)
			if result.company_id.parent_id:
				companies.append(result.company_id.parent_id.id)
		if result.email and result.customer == True:
			result.is_cus = True
			v = {
				'active': True,
				'login': result.email,
				'company_id': result.company_id.id,
				'partner_id': result.id,
				'groups_id': [(6, 0, [group_id])],
				'company_ids':[(6,0,companies)]

			}
			user_id = self.env['res.users'].sudo().create(v)
		if result.email and result.contractor == True:
			v = {
				'active': True,
				'login': result.email,
				'company_id': result.company_id.id,
				'partner_id': result.id,
				'groups_id': [(6, 0, [group_id_contractor])],
				'company_ids': [(6, 0, companies)]

			}
			user_id = self.env['res.users'].sudo().create(v)
		if user_id != False:
			result.current_user = user_id.id

		return result



	@api.multi
	def unlink(self):
		for rec in self:
			user = self.env['res.users'].search([('partner_id','=',rec.id)])
			user.sudo().unlink()
		result = super(ResPartner, self).unlink()
		return result

class MobDetails(models.Model):
	_name = 'mob.details'

	mob_id = fields.Many2one('res.partner')
	mob = fields.Char('Tel NO')



# class ChildrenDetails(models.Model):
#     _name = 'children.details'

#     children_id = fields.Many2one('res.partner')
#     name = fields.Char('Children')
#     dob = fields.Date('DOB')
#     dobch = fields.Selection([
#         ('January','January'),
#         ('February','February'),
#         ('March','March'),
#         ('April','April'),
#         ('May','May'),
#         ('June','June'),
#         ('July','July'),
#         ('Augest','Augest'),
#         ('September','September'),
#         ('October','October'),
#         ('November','November'),
#         ('December','December'),
#     ], string='Month')
#     daysch = fields.Selection([(num, str(num)) for num in range(1,32)], 'Day')
#     yearsch = fields.Selection([(num, str(num)) for num in range(1960,2060)], 'Years')


class JobAssignment(models.Model):
	_name = 'job.assignment'
	_order = 'id desc'


	name = fields.Char('PBA')
	user_id = fields.Many2one('res.partner')
	address1 = fields.Text('Address')
	contact1 = fields.Char('Contact number of Customer')
	contact2 = fields.Char('Contact')
	nick_name = fields.Char('Nick Name',related="user_id.nick_name")
	dob = fields.Date('D.O.B',related="user_id.dob")
	work_type = fields.Char('Type of Work')
	bldng_direction = fields.Char('Facing direction of building')
	area_limit = fields.Char('Initial Area Limit')
	no_stories = fields.Char('No Of Stories')
	assignd_to = fields.Many2one('hr.department','Assigned To')
	location = fields.Many2one('stock.location','Location')
	assignd_by = fields.Many2one('res.users','Assigned By',default=lambda self: self.env.user,readonly=True)
	date_today = fields.Date('Date',default=fields.Date.today)
	activities_line = fields.One2many('event.event','wd_id', domain=[('copy','=',False)])
	tasks_report_all = fields.One2many('task.entry','task_pro')
	my_remarks = fields.Text('Remarks')
	initial_meeting = fields.Date('Expected date of initial meeting')
	final_meeting = fields.Date('Date of Finalisation')
	issuing_submission = fields.Date('Date of issuing Submission File')
	issuing_working = fields.Date('Date of issuing Working File')
	remark1 = fields.Char('Remarks')
	remark2 = fields.Char('Remarks')
	revisions = fields.One2many('rivision.remark','rivision_id')
	project_name = fields.Char('Project Name(Based On Customer Requirement)')
	state = fields.Selection([
		('draft','Draft'),
		('confirm','Confirmed'),
	], string='Status', index=True, readonly=True, default='draft',
		copy=False)
	site_visit_line = fields.One2many('event.event','wd_id')
	latitude= fields.Float(string="Latitude",digits=(16,5))
	longitude = fields.Float(string="Longitude",digits=(16,5))
	branch_name = fields.Many2one('res.company','Branch Name')
	house_name = fields.Char('House Name',related="user_id.house_name")
	street = fields.Char('Street',related="user_id.street")
	street2 = fields.Char('Street2',related="user_id.street2")
	city = fields.Char('City',related="user_id.city")
	state_id = fields.Many2one('res.country.state','State',related="user_id.state_id")
	country_id = fields.Many2one('res.country','Country',related="user_id.country_id")
	project_created = fields.Boolean('Project Created', default=False)

	@api.onchange("branch_name")
	def onchange_branch_name_id(self):
		record = self.env['res.users'].sudo().search([('id','=',self.env.user.id)])
		list = []
		if record.company_id.id == 1:
			branches = self.env['res.company'].sudo().search([])
			for branch in branches:
				list.append(branch.id)
		else:
			for item in record.company_ids:
				list.append(item.id)

		return {'domain': {'branch_name': [('id', 'in', list)]}}



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
	def convert_to_project(self):

		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_project_manager_charge_form')
		view_id = view_ref[1] if view_ref else False
		res = {
			'type': 'ir.actions.act_window',
			'name': _('Manager InCharge'),
			'res_model': 'manager.charge',
			'view_type': 'form',
			'view_mode': 'form',
			'view_id': view_id,
			'target': 'new',
			'context': {'default_rec':self.id,'default_branch':self.branch_name.id}
		}

		return res


	def create(self, cr, uid, vals, context=None):
		if vals.get('name') == False:
			vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'job.assignment', context=context) or '/'
		order =  super(JobAssignment, self).create(cr, uid, vals, context=context)
		return order

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


	@api.multi
	def create_activity(self):
		return{
			'type': 'ir.actions.act_window',
			'name': _('Add Activity'),
			'res_model': 'task.wizard',
			'view_type': 'form',
			'view_mode': 'form',
			# 'view_id': view_id,
			'target': 'new',
			'context': {'default_wd_id':self.id,'default_activity':True}
		}


	@api.multi
	def create_work_site(self):
		return{
			'type': 'ir.actions.act_window',
			'name': _('Add Activity'),
			'res_model': 'task.wizard',
			'view_type': 'form',
			'view_mode': 'form',
			# 'view_id': view_id,
			'target': 'new',
			'context': {'default_wd_id':self.id,'default_site_visit':True}
		}





class ManagerCharge(models.Model):
	_name = 'manager.charge'

	manager = fields.Many2one('res.users','Project Manager')
	project_category = fields.Many2one('project.category','Project Category',required=True)
	branch = fields.Many2one('res.company',string="Branch",required=True,readonly=True)
	rec = fields.Many2one('job.assignment')
	project_name = fields.Char('Project Name')

	@api.onchange("manager")
	def onchange_manager_id(self):
		if self.branch:
			record = self.env['res.users'].sudo().search([])
			list = []
			for rec in record:
				if self.branch.id in [i.id for i in rec.company_ids] or rec.company_id.id == 1:
					if rec.partner_id.is_cus != True:
						list.append(rec.id)

			return {'domain': {'manager': [('id', 'in', list)]}}

	@api.multi
	def confirm_manager(self):
		list = [1]
		group_id_admin2 = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_admin2').id
		group_admin2 = self.env['res.groups'].sudo().search([('id','=',group_id_admin2)])
		for user in group_admin2.users:
			if user.id not in list:
				list.append(user.id)
		if self.manager.id not in list:
			list.append(self.manager.id)

		group_id_general_manager = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_general_manager').id
		group_general_manager = self.env['res.groups'].sudo().search([('id','=',group_id_general_manager)])
		for user in group_general_manager.users:
			if user.id not in list:
				list.append(user.id)

		# print "list=================", list

		period_obj = self.env['project.project']
		# str('PBA/')+str(self.branch.branch_code)+str('/')+str(self.project_category)+str('/')+self.env['ir.sequence'].next_by_code('project.project')[:3]+str('/')+self.env['ir.sequence'].next_by_code('project.project')[-4:]
		# seq = self.env['ir.sequence'].next_by_code('project.project')
		rec = period_obj.sudo().create( {
			'name':self.rec.name,
			'location_id':self.rec.location.id,
			'pba_no':self.rec.name,
			'partner_id':self.rec.user_id.id,
			'no_story':self.rec.no_stories,
			'area':self.rec.area_limit,
			'direction':self.rec.bldng_direction,
			'user_id':self.manager.id,
			'work_nature':self.rec.work_type,
			'latitude':self.rec.latitude,
			'longitude':self.rec.longitude,
			'start_date':fields.Date.today(),
			'project_category':self.project_category,
			'company_id':self.branch.id,
			'members': [(6, 0, list)]
		})
		rec.analytic_account_id.manager_id = self.manager.id
		self.rec.state = 'confirm'
		self.rec.project_created = True


class Rivision(models.Model):
	_name = 'rivision.remark'
	_order = 'rev_date asc'

	name = fields.Char(string="Revision No",compute='_compute_name')
	rivision_id = fields.Many2one('job.assignment')
	pj_id = fields.Many2one('project.project', 'Project')
	# rev_no = fields.Char('Revision No',readonly="True")
	rev_date = fields.Date('Date')
	rivision = fields.Char('Revision Details')
	done_by = fields.Many2one('res.users','Done By')
	remarks = fields.Char('Remarks')



	# @api.model
	def _compute_name(self):
		a = 1        
		for val in self:            
			val.name = str("R/") + str(a)
			a += 1
	


class SiteDetails(models.Model):
	_name = 'site.details'

	user_id = fields.Many2one('res.partner')
	location = fields.Many2one('stock.location','Location')
	survey_no = fields.Char('Survey Number')
	ward = fields.Char('Ward')
	north = fields.Char('North')
	east = fields.Char('East')
	south = fields.Char('South')
	west = fields.Char('West')
	deed_no = fields.Many2one('deed.number','Deed No')
	deed_date = fields.Date('Deed Date')
	nearest_build = fields.Many2one('nearest.building','Nearest Building')
	classification = fields.Char('Classification')
	direction = fields.Char('Direction')
	area_limit = fields.Char('Area Limit')
	budget = fields.Char('Budget')
	no_of_stories = fields.Char('No Of stories')
	attachment = fields.Binary('Attachment If Any')
	anyy = fields.Char('Any')
	extend = fields.Char('Extend')
	remarks = fields.Text('Remarks')




class ProjectTasks(models.Model):
	_name = 'task.entry'
	_order = 'date_today desc'

	@api.multi
	def completed_task(self):
		self.status = 'completed'
		self.state = 'done'

	name = fields.Char('Title')
	sl_no = fields.Integer('No')
	update = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	update_sel = fields.Selection([('not','Not'),('bw','Bw'),('updated','Updated')],default='not')
	task_pro = fields.Integer()
	project_id = fields.Many2one('job.assignment','PBA')
	date_today = fields.Date('Date',default=fields.Date.today())
	status = fields.Selection([('initial','Not Completed'),('completed','Completed')],default="initial",string="Status")
	user_id = fields.Many2one('res.users', 'Assigned to')
	assigned_by = fields.Many2one('res.users', 'Assigned By',readonly=True)
	remarks = fields.Text('Remarks')
	status1 = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	state = fields.Selection([('draft','Draft'),('done','Completed'),('complete','Done')],default="draft")
	admin = fields.Many2one('res.users','Admin')
	updated_user = fields.Many2one('res.users')
	branch = fields.Many2one('res.company',related="project_id.branch_name",store=True)

	_defaults = {
		'assigned_by': lambda obj, cr, uid, ctx=None: uid,
		'admin' : lambda obj, cr, uid, ctx=None: 1,
	}


	@api.onchange('project_id','user_id')
	def onchange_user_id(self):
		if self.project_id and self.user_id:
			flag = 0
			branch_allowed = self.env['res.users'].sudo().search([('id','=',self.user_id.id)])
			for branch in branch_allowed.company_ids:
				if branch.id == self.project_id.branch_name.id:
					flag = 1
				if self.user_id.company_id.id == 1:
					flag = 1
			if flag == 0:
				self.user_id = False
				return {
					'warning': {
						'title': 'Warning',
						'message': "This User Has No Access To The Corresponding Branch"
					}
				}



	@api.multi
	def complete_task(self):
		self.state = 'complete'


	@api.model
	def create(self, vals):
		result = super(ProjectTasks, self).create(vals)
		self.env['popup.notifications'].create({
			'name':result.user_id.id,
			'message':"You have an activity ("+str(result.name)+" )",
			'status':'draft',
		})
		return result



	@api.multi
	def write(self, vals):
		result = super(ProjectTasks, self).write(vals)
		if vals.get('status') and self.env.uid != 1:
			if vals.get('status') == 'completed':
				self.update_sel = 'bw'
				self.updated_user = self.env.user.id

		return result


class NearestBuilding(models.Model):
	_name = 'nearest.building'

	name = fields.Char('Building Name')



class DeedNumber(models.Model):
	_name = 'deed.number'

	name = fields.Char('Number')



class SiteVisit(models.Model):
	_name = 'site.visit'

	site_visit = fields.One2many('site.visit.schedule','site_id')
	user = fields.Many2one('res.users', 'Assigned to')
	pba = fields.Many2one('job.assignment','Related PBA')



	_defaults = {
		'user': lambda obj, cr, uid, ctx=None: uid,
	}




class SiteVisitSchedule(models.Model):
	_name = 'site.visit.schedule'
	_order = 'date_today desc'


	@api.model
	def create(self, vals):
		result = super(SiteVisitSchedule, self).create(vals)
		self.env['popup.notifications'].create({
			'name':result.visit_by.id,
			'message':"You have a Site Visit to "+str(result.location.name),
			'status':'draft',

		})
		return result

	@api.multi
	def write(self, vals):
		result = super(SiteVisitSchedule, self).write(vals)
		if vals.get('status') and self.env.uid != 1:
			if vals.get('status') == 'visited':
				self.update_sel = 'bw'
				self.updated_user = self.env.user.id
		return result

	@api.multi
	def completed_task(self):
		self.status = 'visited'
		self.state = 'done'

	site_id = fields.Many2one('site.visit',store=True)
	update = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	name = fields.Char('Stage Of Work')
	date_today = fields.Date('Date Of Visit',default=fields.Date.today())
	assigned = fields.Many2one('res.users','Assigned By',readonly=True)
	visit_by = fields.Many2one('res.users','Assigned To')
	location = fields.Many2one('stock.location','Location Of Site')
	remarks = fields.Text('Remarks')
	update_sel = fields.Selection([('not','Not'),('bw','Bw'),('updated','Updated')],default='not')
	pba = fields.Many2one('job.assignment','Related PBA',)
	status = fields.Selection([
		('notvisited','Not Visited'),
		('visited','Visited'),
	], string='Status', default='notvisited',
		copy=False)
	admin = fields.Many2one('res.users','Admin')
	updated_user = fields.Many2one('res.users')
	branch = fields.Many2one('res.company',related="pba.branch_name",store=True)
	status1 = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
	state = fields.Selection([('draft','Draft'),('done','Completed'),('complete','Done')],default="draft")

	_defaults = {
		'assigned': lambda obj, cr, uid, ctx=None: uid,
		'admin': lambda obj, cr, uid, ctx=None: 1,
	}


	@api.onchange('pba','visit_by')
	def onchange_visit_by(self):
		if self.pba and self.visit_by:
			flag = 0
			branch_allowed = self.env['res.users'].sudo().search([('id','=',self.visit_by.id)])
			for branch in branch_allowed.company_ids:
				if branch.id == self.pba.branch_name.id:
					flag = 1
			if self.visit_by.company_id.id == 1:
				flag = 1
			if flag == 0:
				self.visit_by = False
				return {
					'warning': {
						'title': 'Warning',
						'message': "This User Has No Access To The Corresponding Branch"
					}
				}


	@api.multi
	def complete_task(self):
		self.state = 'complete'


class event_type(models.Model):
    _inherit = 'event.type'

    eval_line1 = fields.One2many('evaluate.line1', 'eval_id1', string="Evaluate Line")
    eval_line2 = fields.One2many('evaluate.line2', 'eval_id2', string="Evaluate Line")

class EvaluateLine1(models.Model):
	_name = 'evaluate.line1'

	eval_id1 = fields.Many2one('event_type', string="Evaluate")
	name = fields.Char(string="Description")
	# priority = fields.Selection(AVAILABLE_PRIORITIES, string='Priority', select=True)

class EvaluateLine2(models.Model):
	_name = 'evaluate.line2'

	eval_id2 = fields.Many2one('event_type', string="Evaluate")
	name = fields.Char(string="Description")
	# priority = fields.Selection(AVAILABLE_PRIORITIES_THREE, string='Priority', select=True)


	
			
