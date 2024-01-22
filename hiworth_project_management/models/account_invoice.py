from openerp import models, fields, api
from datetime import datetime, time, timedelta
import datetime
import time
from dateutil.relativedelta import relativedelta 


to_19 = ( 'Zero',  'One',   'Two',  'Three', 'Four',   'Five',   'Six',
		  'Seven', 'Eight', 'Nine', 'Ten',   'Eleven', 'Twelve', 'Thirteen',
		  'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen' )
tens  = ( 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety')
denom = ( '',
		  'Thousand',     'Million',         'Billion',       'Trillion',       'Quadrillion',
		  'Quintillion',  'Sextillion',      'Septillion',    'Octillion',      'Nonillion',
		  'Decillion',    'Undecillion',     'Duodecillion',  'Tredecillion',   'Quattuordecillion',
		  'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Novemdecillion', 'Vigintillion' )


class AccountInvoice(models.Model):
	_inherit = 'account.invoice'

	@api.multi
	def get_mode(self,invoice_id,no):
		if invoice_id:
			mode = ''
			date = ''
			rec = self.env['account.invoice'].search([('id','=',invoice_id)])
			if rec:
				for vals in rec.payment_ids:
					mode = str(vals.journal_id.name)
					date = str(vals.date)
			if no == 0:  
				return mode
			if no == 1:
				return date





	@api.multi
	def _convert_nn(self, val):
		"""convert a value < 100 to English.
		"""
		if val < 20:
			return to_19[val]
		for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
			if dval + 10 > val:
				if val % 10:
					return dcap + '-' + to_19[val % 10]
				return dcap
	@api.multi
	def _convert_nnn(self, val):
		"""
			convert a value < 1000 to english, special cased because it is the level that kicks
			off the < 100 special case.  The rest are more general.  This also allows you to
			get strings in the form of 'forty-five hundred' if called directly.
		"""
		word = ''
		(mod, rem) = (val % 100, val // 100)
		if rem > 0:
			word = to_19[rem] + ' Hundred'
			if mod > 0:
				word += ' '
		if mod > 0:
			word += self._convert_nn(mod)
		return word

	@api.multi
	def english_number(self, val):
		if val < 100:
			return self._convert_nn(val)
		if val < 1000:
			 return self._convert_nnn(val)
		for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
			if dval > val:
				mod = 1000 ** didx
				l = val // mod
				r = val - (l * mod)
				ret = self._convert_nnn(l) + ' ' + denom[didx]
				if r > 0:
					ret = ret + ', ' + self.english_number(r)
				return ret

	@api.multi
	def amount_to_text(self, number, currency):
		number = '%.2f' % number
		units_name = currency
		list = str(number).split('.')
		start_word = self.english_number(int(list[0]))
		end_word = self.english_number(int(list[1]))
		cents_number = int(list[1])
		cents_name = (cents_number > 1) and 'Paise' or 'Paise'

		return ' '.join(filter(None, [start_word, units_name, (start_word or units_name) and (end_word or cents_name) and 'and', end_word, cents_name]))


	@api.model
	def create(self,vals):
		result = super(AccountInvoice, self).create(vals)
		code = self.env['ir.sequence'].next_by_code('account.invoice')
		date = datetime.datetime.today()
		date_yr = date.year
		date_mnth = date.month
		if date_mnth < 10:
			date_mnth = '0'+str(date_mnth)
		result['prime_invoice'] =  str('PBA')+'/'+str(vals.get('type_id'))+'/'+str(date_mnth)+str(date_yr)[2:] +'/'+code
		
		return result

	@api.multi
	def invoice_print(self):
		
		assert len(self) == 1
		self.sent = True
		return self.env['report'].get_action(self, 'hiworth_project_management.report_invoice5')