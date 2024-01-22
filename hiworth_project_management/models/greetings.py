from openerp import models, fields, api
import datetime
from lxml import etree
import math
import pytz
import threading
import urlparse

from openerp.osv import osv
from datetime import datetime, timedelta
from openerp.tools.translate import _
from openerp import SUPERUSER_ID
import openerp.addons.decimal_precision as dp
from openerp import http
from openerp.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
AVAILABLE_PRIORITIES = [
	('0', 'Priority'),
	('1','Prior')
]


class Greetings(models.Model):
	_name = 'greetings.prime'

	name = fields.Char('Greetings Name',required=True)
	date_greet = fields.Date('Greetings Date',required=True)


	def _cron_special_day_reminder(self, cr, uid, context=None):
		su_id =self.pool.get('res.partner').browse(cr, uid, SUPERUSER_ID)
		partners1 = self.pool.get('res.partner')
		partners = partners1.search(cr, uid, (), context=None)
		greetings = self.search(cr, uid, (), context=None)
		for greeting in self.browse(cr, uid, greetings, context=None):
			if greeting.date_greet != False:
				greet_day = datetime.strptime(greeting.date_greet,'%Y-%m-%d').date()
				today =datetime.now().date()
				if greet_day.month == today.month:
					if greet_day.day == today.day:
						for partner_obj in partners:
							partner = self.pool.get('res.partner').browse(cr,uid,partner_obj,context=None)
							if partner.email:
								template_id = self.pool.get('ir.model.data').get_object_reference(cr, uid,
																	  'hiworth_project_management',
																	  'email_template_edi_special_day_reminder')[1]
								email_template_obj = self.pool.get('email.template')
								if template_id:
									values = email_template_obj.generate_email(cr, uid,template_id, partner.id, context=context)
									values['email_from'] = su_id.email
									values['email_to'] = partner.email
									values['res_id'] = False
									if not values['subject']:
										values['subject'] = str(greeting.name)+' '+str('Greetings')
									mail_mail_obj = self.pool.get('mail.mail')
									msg_id = mail_mail_obj.create(cr, SUPERUSER_ID,values)
									if msg_id:
										mail_mail_obj.send(cr, SUPERUSER_ID,[msg_id])

		return True


class Feedback(models.Model):
	_name = 'feedback.prime'
	_order = 'id desc'

	name = fields.Many2one('res.users')
	date = fields.Date('Date',default=fields.Date.today)
	email = fields.Char('Email',related="name.login")
	recmnd1 = fields.Boolean()
	recmnd2 = fields.Boolean()
	recmnd3 = fields.Boolean()
	recmnd4 = fields.Boolean()
	recmnd5 = fields.Boolean()
	customer_care1 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	customer_care2 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	customer_care3 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	customer_care4 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	customer_care5 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	response1 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	response2 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	response3 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	response4 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	response5 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	details1 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	details2 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	details3 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	details4 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	details5 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	coordination1 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	coordination2 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	coordination3 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	coordination4 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	coordination5 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	on_time1 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	on_time2= fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	on_time3 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	on_time4 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	on_time5 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	site1 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	site2 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	site3 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	site4 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	site5 = fields.Selection(AVAILABLE_PRIORITIES, 'Priority')
	remarks = fields.Text('REMARKS')
	grivences = fields.Text('GRIVENCES')
	state = fields.Selection([('draft','Draft'),('submit','Submitted')],default="draft")

	_defaults = {
		'name':lambda obj, cr, uid, ctx=None: uid,
		}


	@api.multi
	def submit_feedback(self):
		self.state = 'submit'

	def _cron_feedback_reminders(self, cr, uid, context=None):
		user_all = self.pool.get('res.users')
		message = self.pool.get('im_chat.message.req')
		users = user_all.search(cr, uid, (), context=None)
		for partner_obj in users:
			user = self.pool.get('res.users').browse(cr,uid,partner_obj,context=None)
			if user.partner_id.customer == True:
				message.create(cr,uid,{'from_id':1,
											'message_type':'general',
											'no_edit':True,
											'cc_id':user.id,
											'to_id':user.id,
											'date_today':fields.Datetime.now(),
											'message':str("Hi")+" "+str(user.name)+"\n\n"+str("Please Fill This Feedback By Clicking The Below Link:\n Login with your credentials & Create a feedback..\n Thank You\n\n")+"\n\n"+str("Link is \n\nhttp://primeerp.org/web#page=0&limit=80&view_type=list&model=feedback.prime&menu_id=579&action=689")

															}, context=None)
		return True

