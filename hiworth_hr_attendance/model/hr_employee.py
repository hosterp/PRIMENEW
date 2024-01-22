from openerp import models, fields, api
from openerp import exceptions
from openerp.exceptions import except_orm, Warning, RedirectWarning
import dateutil.parser
from dateutil import relativedelta
import time
from datetime import datetime,timedelta
AVAILABLE_PRIORITIES = [
    ('0', 'Very Low'),
    ('1', 'Low'),
    ('2', 'Normal'),
    ('3', 'High'),
    ('4', 'Very High'),
    ('5', 'Excellent')
]


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    new_owner = fields.Char('Account Owner')




class HrJob(models.Model):
    _inherit = 'hr.job'

    code = fields.Char('Code',required=False)

class BranchProject(models.Model):
    _name = 'branch.project'

    name = fields.Char('Branch Name',required=True)
    code = fields.Char('Code',required=True)

class TaskRateLine(models.Model):
    _name = 'task.rate.line'

    date = fields.Datetime('Date')
    rate_id = fields.Many2one('hr.employee', domain=[('status1','=','active')])
    task_id = fields.Many2one('event.event')
    average = fields.Float('Average')

class HrEmployee(models.Model):
    _inherit='hr.employee'


    @api.multi
    def change_password(self):
        for rec in self:
            return {
                    'name': rec.name,
                    'view_mode': 'form,tree',
                    'res_model': 'hr.password.reset',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    "context": {'default_employee_id': rec.id,'default_user_id': rec.user_id.id,}
                }
        user_id = rec.user_id
        user_id.write({'password': "admin3"})

    task_rate_line = fields.One2many('task.rate.line','rate_id')
    user_category = fields.Many2one('res.groups',string="User Category",required=True)


    @api.model

    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(HrEmployee, self).fields_view_get(view_id=view_id,view_type=view_type,toolbar=toolbar,submenu=submenu)
        if res.get('toolbar', False) and res.get('toolbar').get('print', False):
            reports = res.get('toolbar').get('print')
            for report in reports:
                if report.get('string') == 'Attendance Error Report':
                    res['toolbar']['print'].remove(report)
        return res



    @api.multi
    @api.depends('task_rate_line')
    def get_last_three_mnths_rating(self):
        for line in self:
            rec_count = 0
            rate_total = 0
            three_months_back = datetime.today()+dateutil.relativedelta.relativedelta(months=-3)
            for rate in line.task_rate_line:
                if datetime.strptime(rate.date, "%Y-%m-%d %H:%M:%S") >= three_months_back:
                    rec_count  += 1
                    rate_total += rate.average
            if rate_total != 0:
                line.last_three_rating = rate_total/rec_count
                line.last_three_rating_priority =str(int(round(rate_total/rec_count)))

    attendance_ids = fields.One2many('hiworth.hr.attendance', 'name')
    # current_branch = fields.Many2one('res.company','Current Branch',required=True)
    branch_id = fields.Many2many('res.company',string='Allowed Branches')
    emp_code = fields.Char('Order Reference', required=False, copy=False,readonly=False,)
    street = fields.Char('Street')
    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state')
    zip = fields.Char('Zip')
    street2 = fields.Char()
    street1 = fields.Char('Street')
    city1 = fields.Char('City')
    state_id1 = fields.Many2one('res.country.state')
    zip1 = fields.Char('Zip')
    street3 = fields.Char()
    country_id1 = fields.Many2one('res.country')
    type_of_card = fields.Selection([('passport','Passport'),('aadharcard','Aadhar Card'),('voterid','VoterId'),('pancard','PanCard'),('license','License')],string="Type Of Card")
    present = fields.Boolean(default=False)
    location = fields.Many2one('stock.location','Location')
    monthly_leave = fields.Float('Monthly Leave Taken')
    father = fields.Char('Name Of Father')
    mother = fields.Char('Name Of Mother')
    hus_wife = fields.Char('Name Of Husband/Wife')
    joining_date = fields.Date('Date Of Joining')
    employee_type = fields.Selection([('trainee','Trainee'),('employee','Employee'),('manager','Manager'),('others','Others')],'Employee Type')
    worker_type = fields.Selection([('mason','Mason'),('helper','Helper')],'Worker Type')
    edu_qualify = fields.One2many('edu.qualify','edu_id')
    wedding_anniversary = fields.Date('Wedding Anniversary')
    last_three_rating = fields.Float(compute="get_last_three_mnths_rating")
    last_three_rating_priority = fields.Selection(AVAILABLE_PRIORITIES, 'Priority', select=True,compute="get_last_three_mnths_rating") 
    manager_req = fields.Boolean(compute="_get_manager_req")
    reset_pswd = fields.Boolean(default=False)
    branch_visibility = fields.Boolean(default=False)
    street_branch = fields.Char('Street',related="company_id.street")
    street2_branch = fields.Char('Street2',related="company_id.street2")
    city_branch = fields.Char('City',related="company_id.city")
    state_id_branch = fields.Many2one('res.country.state','State',related="company_id.state_id")
    zip_branch = fields.Char('Zip',related="company_id.zip")
    country_id_branch = fields.Many2one('res.country','Country',related="company_id.country_id")
    status1 = fields.Selection([('active','Active'),
                                ('request_resign','Resignation Requested'),
                                # ('approved_by_manager','Approved BY Manager'),
                                # ('approved_by_dgm','Approved BY DGM'),
                                # ('approved_by_gm','Approved BY GM'),
                                # ('approved_by_admin2','Approved BY Admin2'),
                                ('resign','Resigned')], default="active", string="State")

    bank_details = fields.Text("Bank Details")





    @api.multi
    def view_action_employee_resign(self):
        # if self.env.user.employee_id.id == self.id:
        self.status1 = 'request_resign'
        user = self.env['res.users'].search([])
        for u in user:
            if u.has_group('hiworth_project_management.group_admin1') or u.has_group(
                    'hiworth_project_management.group_admin2') or u.has_group(
                    'hiworth_project_management.group_general_manager') or u.has_group(
                    'hiworth_project_management.group_dgm'):

                self.env['popup.notifications'].create({
                    'name': u.id,
                    'status': 'draft',
                    'message': "You have a resignation request to approve"})
        # else:
        #     raise Warning("Only can request resignation for your self..")

    @api.multi
    def view_action_resign(self):
        if self.env.user.employee_id.id != self.id:
            res = {
            'name': 'Resignation',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hr.employee.resignation',
            # 'domain': [('line_id', '=', self.id),('date','=',self.date)],
            # 'res_id': res_id,
            'target': 'new',
            'type': 'ir.actions.act_window',
            'context': {'default_resign_id': self.id},

            }

            return res

        else:

            raise Warning("You can't approve your resignation request...")


    @api.onchange('user_category')
    def onchange_user_category(self):
        if self.user_category:
            list = []
            group_id_admin1 = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_admin1').id
            list.append(group_id_admin1)
            group_id_admin2 = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_admin2').id
            list.append(group_id_admin2)
            group_general_manager = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_general_manager').id
            list.append(group_general_manager)
            if self.user_category.id in list:
                self.branch_visibility = True
            else:
                self.branch_visibility = False



    @api.one
    @api.depends('company_id')
    def _get_manager_req(self):
        if self.company_id:
            if self.company_id.id == 1:
                self.manager_req = True

    @api.onchange('company_id','parent_id')
    def onchange_parent_id_branch(self):
        if self.company_id and self.parent_id:
            rec = self.env['res.users'].sudo().search([('employee_id','=',self.parent_id.id)])
            flag = 0
            if rec.company_id.id == self.company_id.id:
                flag = 1
            # for branch in rec.company_ids:
            #     if branch.id == self.current_branch:
            #         flag == 1
            if 1 in [i.id for i in rec.company_ids]:
                flag = 1
            if self.company_id.id == 1:
                flag = 1
            if flag == 0:
                self.parent_id = False
                return {
               'warning': {
                   'title': 'Warning',
                   'message': "This User Has No Access To The Corresponding Branch"
                            }
                       }


    @api.multi
    def unlink(self):
        for rec in self:
            rec.active = False
        return

    @api.multi
    def get_employee_code(self, o):
        return self.env['hr.employee'].search([('id','=',o.id)]).emp_code

    @api.multi 
    def get_location_ml(self,o,day):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id)])
        for r in rec:
            if dateutil.parser.parse(r.sign_in).date() == day[0]:
                return r.location.name



    @api.model
    def create(self, vals):   
        result = super(HrEmployee, self).create(vals)
        if result.emp_code == False:
            result.emp_code = str('PBA/')+str(result.company_id.branch_code) if result.company_id.branch_code else ''+str('/') + self.env['ir.sequence'].next_by_code('hr.employee')[3:] or '/'

        if result.user_category:
            group = []
            group.append(result.user_category.id)
        

        if result.work_email:
            ids = []
            ids.append(result.company_id.id)
            if result.branch_id:
                for vals in result.branch_id:
                    ids.append(vals.id)
            
            v = {
             'active': True,
             'name': result.name,
             'login': result.work_email,
             'company_id':result.company_id.id,
             'company_ids': [(6, 0, ids)],
             'image':result.image_medium,
             'employee_id':result.id,
             'groups_id': [(6, 0, group)]
            
            }
            user_id1 = self.env['res.users'].sudo().create(v)
            result.user_id = user_id1.id
    

        return result

    @api.multi
    def write(self, vals):
        result = super(HrEmployee, self).write(vals)
        rec = self.env['res.users'].sudo().search([('employee_id','=',self.id)])
        if rec and rec.id !=1:
            list = [i.id for i in rec.company_ids]
            list1 = []
            if vals.get('name'):
                rec.write({'name':vals.get('name')})
            if vals.get('image_medium'):
                rec.write({'image':vals.get('image_medium')})
            if vals.get('company_id') and not vals.get('branch_id'):
                if vals.get('company_id') in list:
                    rec.write({'company_id':vals.get('company_id')})
                else:
                    list.append(vals.get('company_id'))
                    rec.write({'company_ids':[(6,0, list)],'company_id':vals.get('company_id')})
            if vals.get('branch_id') and not vals.get('company_id'):
                list1 = vals.get('branch_id')[0][2]
                list1.append(rec.company_id.id)
                rec.write({'company_ids':[(6,0,list1)]})
            if vals.get('company_id') and vals.get('branch_id'):
                list1 = vals.get('branch_id')[0][2]
                list1.append(vals.get('company_id'))
                list.append(vals.get('company_id'))
                rec.write({'company_id':vals.get('company_id'),'company_ids':[(6,0,list1)]})


        return result


    @api.multi
    def load_employee_attendance(self):
        return {
                    'name': self[0].name,
                    'view_mode': 'form,tree',
                    'res_model': 'hiworth.hr.attendance',
                    'type': 'ir.actions.act_window',
                    "views": [[self.env.ref("hiworth_hr_attendance.hiworth_hr_attendance_view_employee_attendance_tree").id, "tree"], [False, "form"]],
                    'domain': [('name','=',self[0].id)],
                    "context": {'default_name': self[0].id}
                }
class HrPasswordReset(models.Model):
    _name = 'hr.password.reset'

    employee_id = fields.Many2one('hr.employee',domain=[('status1','=','active')])
    user_id = fields.Many2one('res.users')
    new_password = fields.Char('New Password')

    @api.multi
    def change_password(self):
        for rec in self:
            rec.employee_id.reset_pswd = True
            user_id = rec.user_id
            user_id.write({'password': rec.new_password})



class EduQualify(models.Model):
    _name = 'edu.qualify'

    edu_id = fields.Many2one('hr.employee',domain=[('status1','=','active')])
    qualification = fields.Char('Qualification')
    year = fields.Char('Year Of Passing')
    unvrsty = fields.Char('University/College')

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    lop_emp = fields.Float(string="Loss Of Pay/Not")

    # @api.model
    # def create(self, vals):
    #     result = super(HrHolidays, self).create(vals)
    #     print "typeeeeeeeeeeeeeeeee", result.type
    #     if result.type == 'remove':
    #         result.employee_id.monthly_leave += result.number_of_days_temp
    #     # if result.number_of_days_temp > result.employee_id.monthly_leave:
    #     #     raise exceptions.ValidationError('You have not enough leave ')
    #     # result.employee_id.monthly_leave = result.employee_id.monthly_leave - result.number_of_days_temp
    #     return result



    def holidays_validate(self):
        obj_emp = self.env['hr.employee']
        ids2 = obj_emp.search( [('user_id', '=', self.env.user.id)])
        manager = ids2 and ids2[0] or False
        self.write({'state':'validate'})
        # if self.type == 'remove':
        #     self.employee_id.monthly_leave += self.number_of_days_temp
        data_holiday = self.browse()
        for record in data_holiday:
            if record.double_validation:
                self.write(cr, uid, [record.id], {'manager_id2': manager})
            else:
                self.write(cr, uid, [record.id], {'manager_id': manager})
            if record.holiday_type == 'employee' and record.type == 'remove':
                meeting_obj = self.pool.get('calendar.event')
                meeting_vals = {
                    'name': record.name or _('Leave Request'),
                    'categ_ids': record.holiday_status_id.categ_id and [(6,0,[record.holiday_status_id.categ_id.id])] or [],
                    'duration': record.number_of_days_temp * 8,
                    'description': record.notes,
                    'user_id': record.user_id.id,
                    'start': record.date_from,
                    'stop': record.date_to,
                    'allday': False,
                    'state': 'open',            # to block that meeting date in the calendar
                    'class': 'confidential'
                }   
                #Add the partner_id (if exist) as an attendee             
                if record.user_id and record.user_id.partner_id:
                    meeting_vals['partner_ids'] = [(4,record.user_id.partner_id.id)]
                    
                ctx_no_email = dict(context or {}, no_email=True)
                meeting_id = meeting_obj.create( meeting_vals)
                self._create_resource_leave([record])
                self.write(cr, uid, ids, {'meeting_id': meeting_id})
            elif record.holiday_type == 'category':
                emp_ids = obj_emp.search( [('category_ids', 'child_of', [record.category_id.id])])
                leave_ids = []
                batch_context = dict(mail_notify_force_send=False)
                for emp in obj_emp.browse(emp_ids):
                    vals = {
                        'name': record.name,
                        'type': record.type,
                        'holiday_type': 'employee',
                        'holiday_status_id': record.holiday_status_id.id,
                        'date_from': record.date_from,
                        'date_to': record.date_to,
                        'notes': record.notes,
                        'number_of_days_temp': record.number_of_days_temp,
                        'parent_id': record.id,
                        'employee_id': emp.id
                    }
                    leave_ids.append(self.create(vals))
                for leave_id in leave_ids:
                    # TODO is it necessary to interleave the calls?
                    for sig in ('confirm', 'validate', 'second_validate'):
                        self.signal_workflow([leave_id], sig)
        return True


    @api.multi
    def approve_leave(self):
        view_id = self.env.ref('hiworth_hr_attendance.view_wizard_approve_lop').id
        return {
            'name':'Loss Of Pay',
            'view_type':'form',
            'view_mode':'form',
            'res_model':'loss.pay',
            'view_id': False,
            'views': [(view_id, 'form'),],
            # 'view_id':view_id,
            'type':'ir.actions.act_window',
            'target':'new',
            'context':{'default_rec': self.id,'default_name':self.number_of_days_temp},
        }
       
        


class LossPay(models.Model):
    _name = 'loss.pay'

    name = fields.Float(string="Loss Of Pay/Not")
    rec = fields.Many2one('hr.holidays')

    @api.multi
    def confirm_edit(self):
        self.rec.holidays_validate()
        self.rec.lop_emp = self.name
       

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    lop = fields.Float('Loss Of Pay Days', compute="_onchange_lop")
    advance = fields.Float('Advance',compute="_compute_advance_amount")

    @api.depends('employee_id')
    def _compute_advance_amount(self):
        recs = self.env['hr.holidays'].search([('employee_id','=',self.employee_id.id),('date_from','>=',self.date_from),('date_to','<=',self.date_to)])
        for rec in recs:
            self.lop += rec.lop_emp

    # _defaults = {
    #     'date_from': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=-1, day=1, days=15))[:10],
    #     'date_to': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+0, day=1, days=14))[:10],
        
    # }

    @api.depends('employee_id')
    def _onchange_lop(self):
        recs = self.env['advance.pay'].search([])
        print "recssssss===============", recs
        date_today = fields.Date.today()
        for rec in recs:
            if datetime.strptime(rec.date, "%Y-%m-%d").month == datetime.strptime(date_today, "%Y-%m-%d").month and datetime.strptime(rec.date, "%Y-%m-%d").year == datetime.strptime(date_today, "%Y-%m-%d").year:
                print "year month ok=================="
                for lines in rec.advance_line:
                    if lines.employee.id == self.employee_id.id:
                        self.advance += lines.amount
            return
            # print "rec.date.month==============", rec.date.month
            # print "fields.Date.today().month============", fields.Date.today().month
            # if rec.date.month == fields.Date.today().month:
                # print "aaaaaaaaaaa====================="
                # pass
class HrEmployeeResignation(models.TransientModel):
    _name='hr.employee.resignation'

    resign_id =fields.Many2one('hr.employee',domain=[('status1','=','active')])
    resign_date = fields.Date('Released Date', default=fields.Date.today)

    @api.multi
    def button_confirm(self):
        self.resign_id.resigning_date = self.resign_date
        self.resign_id.status1 = 'resign'
        user = self.env['res.users'].search([('login', '=', self.resign_id.work_email)])
        if user:
            user.active = False
        

