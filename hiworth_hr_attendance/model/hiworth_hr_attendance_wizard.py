from openerp import models, fields, api,_
from openerp import exceptions
from openerp.osv import osv


class SigninWizard(models.TransientModel):
    _name = 'hiworth.hr.signin.wizard'
    employee_ids = fields.Many2many('hr.employee', string='Employees',domain=[('status1','=','active')])
    signin_time = fields.Datetime('Sign In time',default=fields.Datetime.now())
    is_daily_worker = fields.Boolean('Not a permanent Employee?')
    location = fields.Many2one('stock.location','Location')

    @api.multi
    def do_mass_update(self):
        not_updated = []
        self.ensure_one()
        if not (self.signin_time):
            raise exceptions.ValidationError('Please enter sign in time.')
        if self.signin_time:
            if self.location:
                for employee in self.employee_ids:
                    if employee.employee_type == 'worker':
                        employee.location = self.location.id
                    else:
                        raise osv.except_osv(_('Error!'),
                                         _('"%s" is not a worker .') % (employee.name))
            for employee in self.employee_ids:
                rec = self.env['hiworth.hr.attendance'].search([('name','=',employee.id),('sign_out','=',False)])
                if rec:
                    raise osv.except_osv(_('Error!'),
                                         _('"%s" is signed in on "%s" ,Please signout and try again') % (employee.name,rec.sign_in))
                # prvs_data = self.env['hiworth.hr.attendance'].search([('name','=',employee.id),('sign_in','<=',self.signin_time),('sign_out','>=',self.signin_time)])
                # if prvs_data:
                #     raise osv.except_osv(_('Error!'),
                #                          _('"%s" is already signed in on "%s" ') % (employee.name,self.signin_time))
                employee.present = True
                if employee.worker_type:
                    wrkr_type = employee.worker_type
                else:
                    wrkr_type = employee.employee_type

                result = self.env['hiworth.hr.attendance'].sudo().create({'sign_in': self.signin_time, 'state': 'sign_in', 'sign_out': False, 'name': employee.id,'location':self.location.id,'employee_type':wrkr_type})
                if isinstance(result, int):
                    not_updated.append(result)
        return True

class SignoutWizard(models.TransientModel):
    _name = 'hiworth.hr.signout.wizard'
    employee_ids = fields.Many2many('hr.employee', string='Employees',domain=[('status1','=','active')])
    signout_time = fields.Datetime('Sign Out time',default=fields.Datetime.now())

    @api.multi
    def do_mass_update(self):
        # not_updated = []
        self.ensure_one()
        if not (self.signout_time):
            raise exceptions.ValidationError('Please enter sign out time')
        if self.signout_time:
            for employee in self.employee_ids:
            	rec = self.env['hiworth.hr.attendance'].search([('name','=',employee.id),('state','=','sign_in')])
                employee.state = 'absent'
                employee.present = False
                employee.location = ''
                rec.state = 'sign_out'
                rec.sign_out = self.signout_time
                # result = self.env['hiworth.hr.attendance'].create({'sign_in': False, 'state': 'sign_out', 'sign_out': self.signout_time, 'name': employee.id})
                # if isinstance(result, int):
                #     not_updated.append(result)
        return True
