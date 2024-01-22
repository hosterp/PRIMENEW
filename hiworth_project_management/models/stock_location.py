from openerp import models, fields, api
import urllib
from openerp import tools
from openerp.tools.translate import _



try:
	import simplejson as json
except ImportError:
	import json



class StockLocation(models.Model):
	_inherit = 'stock.location'

	latitude= fields.Float(string="Latitude",digits=(16,5))
	longitude = fields.Float(string="Longitude",digits=(16,5)) 
	name = fields.Char('Location Name', required=True, translate=False)



	@api.multi
	def show_google_map(self):
		myurl='https://www.google.co.in/maps/@{},{},15z'.format(self.latitude,self.longitude),
		return {
				'name':"google",

				'type':'ir.actions.act_url',
				
				'target':'new',
				'url':myurl

		}
                

        