from openerp import models, fields, api

class AdminConfiguration(models.Model):
	_inherit = 'res.groups'

	ready_bool = fields.Boolean(default=False)
	user_categ = fields.Boolean(default=False)