from openerp import models, fields, api

class HrContract(models.Model):
	_inherit = 'hr.contract'

	hra = fields.Float('HRA')
	other = fields.Float('Other Allowance')

	# schedule_pay = fields.Selection([
 #            ('monthly', 'Monthly'),
 #            ('daily','Daily')
 #            ], 'Scheduled Pay', select=True)
    