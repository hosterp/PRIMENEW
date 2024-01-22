from openerp import models, fields, api
import time

from openerp import SUPERUSER_ID


class IrRule(models.Model):
	_inherit = 'ir.rule'

	def _eval_context(self, cr, uid):
		"""Returns a dictionary to use as evaluation context for
		   ir.rule domains."""
		list_admin2 = []
		list_gm = []
		list_dgm = []
		list_mo = []
		list_am = []
		list_super_employee = []

		group_id_admin1 = self.pool.get('ir.model.data').get_object(cr,uid,'hiworth_project_management',  'group_admin1')
		group_id_admin2 = self.pool.get('ir.model.data').get_object(cr,uid,'hiworth_project_management',  'group_admin2')
		group_id_gm = self.pool.get('ir.model.data').get_object(cr,uid,'hiworth_project_management',  'group_general_manager')
		group_id_dgm = self.pool.get('ir.model.data').get_object(cr,uid,'hiworth_project_management',  'group_dgm')
		group_id_mo = self.pool.get('ir.model.data').get_object(cr,uid,'hiworth_project_management',  'group_manager_office')
		group_id_am = self.pool.get('ir.model.data').get_object(cr,uid,'hiworth_project_management',  'group_am_office')

		# if group_id_admin1.id not in list_admin2:
		list_admin2.append(group_id_admin1.id)

		list_gm.append(group_id_admin1.id)
		list_gm.append(group_id_admin2.id)

		list_dgm.append(group_id_admin1.id)
		list_dgm.append(group_id_admin2.id)
		list_dgm.append(group_id_gm.id)

		list_mo.append(group_id_admin1.id)
		list_mo.append(group_id_admin2.id)
		list_mo.append(group_id_gm.id)
		list_mo.append(group_id_dgm.id)


		list_am.append(group_id_admin1.id)
		list_am.append(group_id_admin2.id)
		list_am.append(group_id_gm.id)
		list_am.append(group_id_dgm.id)
		list_am.append(group_id_mo.id)


		list_super_employee.append(group_id_admin1.id)
		list_super_employee.append(group_id_admin2.id)
		list_super_employee.append(group_id_gm.id)
		list_super_employee.append(group_id_dgm.id)
		list_super_employee.append(group_id_mo.id)
		list_super_employee.append(group_id_am.id)


		return {'user': self.pool.get('res.users').browse(cr, SUPERUSER_ID, uid),
				'time':time,
				'admin2':list_admin2,
				'gm':list_gm,
				'dgm':list_dgm,
				'mo':list_mo,
				'am':list_am,
				'se':list_super_employee}
