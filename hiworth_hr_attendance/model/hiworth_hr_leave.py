from openerp import models, fields, api
import datetime, calendar, ast
import dateutil.parser


class HiworthHrLeave(models.Model):
    _name = 'hiworth.hr.leave'

    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))
    type_selection=fields.Selection([('approved','Approved'),('confirm','Confirmed'),('both','Both')], default='approved')
    attendance_type=fields.Selection([('daily','Daily'),('weekly','Weekly'),('monthly','Monthly')], default='monthly')
    active_ids=fields.Char()

    @api.multi
    def get_employee_code(self, o):
        return self.env['hr.employee'].search([('id','=',o.id)]).emp_code

    @api.multi 
    def get_location_ml(self,o,day):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id)])
        for r in rec:
            if dateutil.parser.parse(r.sign_in).date() == day[0]:
                return r.location.name

    @api.multi
    def get_employee_location(self, o, date):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id)])
        # ,('sign_in','>=',date),('sign_out','<=',date)
        for r in rec:
            if str(dateutil.parser.parse(r.sign_in).date()) == date:
                return r.location.name


    @api.onchange('attendance_type')
    def _onchange_attendance_type(self):
        if self.attendance_type:
            if self.attendance_type == 'daily':
                self.from_date = fields.date.today()
                self.to_date = fields.date.today()

    # Calculate default time ranges
    @api.model
    def default_time_range(self, type):
        year = datetime.date.today().year
        month = datetime.date.today().month
        last_day = calendar.monthrange(datetime.date.today().year,datetime.date.today().month)[1]
        first_day = 1
        if type=='from':
            return datetime.date(year, month, first_day)
        elif type=='to':
            return datetime.date(year, month, last_day)

    @api.model
    def print_hiworth_hr_leave_summary(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Attendance report filter",
            "res_model": "hiworth.hr.leave",
            "context": {'active_ids': self.env.context.get('active_ids',[])},
            "views": [[False, "form"]],
            "target": "new",
        }

    @api.multi
    def print_hiworth_hr_leave_summary_confirmed(self):
        self.ensure_one()
        hrEmployee = self.env['hr.employee']
        employees = hrEmployee.browse(self.env.context.get('active_ids',[]))
        datas = {
            'ids': employees._ids,
			'model': hrEmployee._name,
			'form': hrEmployee.read(),
			'context':self._context,
        }
        if self.attendance_type == 'monthly':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary',
                'datas': datas,
                'context':{'start_date': self.from_date, 'end_date': self.to_date, 'type_selection': self.type_selection, }
            }
        if self.attendance_type == 'weekly':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary',
                'datas': datas,
                'context':{'start_date': self.from_date, 'end_date': self.to_date, 'type_selection': self.type_selection, }
            }
        if self.attendance_type == 'daily':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary1',
                'datas': datas,
                'context':{'start_date': self.from_date, 'end_date': self.to_date, 'type_selection': self.type_selection, }
            }

    @api.multi
    def view_hiworth_hr_leave_summary_confirmed(self):
        self.ensure_one()
        print 'selfids ', self.env.context.get('active_ids',[])
        self.active_ids=self.env.context.get('active_ids',[])
        if self.attendance_type == 'monthly':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary_view',
                'report_type': 'qweb-html'
            }
        if self.attendance_type == 'weekly':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary_view',
                'report_type': 'qweb-html'
            }
        if self.attendance_type == 'daily':
            return{
                'type' : 'ir.actions.report.xml',
                'report_name' : 'hiworth_hr_attendance.template_hiworth_hr_leave_summary_view1',
                'report_type': 'qweb-html'
            }


    def get_attendance_days(self, id, start_date, end_date):
        return self.env['hr.employee'].get_attendance_days(id, start_date, end_date)

    def get_selected_users(self, active_ids):
        active_ids = ast.literal_eval(active_ids)
        active_ids = [int(i) for i in active_ids]
        print 'active_ids asd ', active_ids
        return self.env['hr.employee'].browse(active_ids)


class HrEmployee(models.Model):
    _inherit='hr.employee'

    @api.multi
    def get_employee_location(self, o, date):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id)])
        # ,('sign_in','>=',date),('sign_out','<=',date)
        for r in rec:
            if str(dateutil.parser.parse(r.sign_in).date()) == date:
                return r.location.name

    # @api.multi
    # def get_employee_location(self, o, date):
    #     rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id),('sign_in','>=',date),('sign_out','<=',date)])
    #     # print "reccccccccccccccccc",
    #     if rec:
    #         return rec.location.name


    @api.model
    def get_attendance_days(self, employee_id, start_date, end_date):
        # Find the list of days for which the report is to be generated
        delta=datetime.datetime.strptime(end_date, "%Y-%m-%d")-datetime.datetime.strptime(start_date, "%Y-%m-%d");
        selected_days=[(datetime.datetime.strptime(start_date, "%Y-%m-%d")+datetime.timedelta(days=day)).date() for day in range(delta.days+1)];
        print "EmployeeiDDDDDDDDDDDDDDDDDDdd", employee_id

        # Find the days for which the employee is present
        recs=self.env['hiworth.hr.attendance'].search([('name','=',employee_id), ('sign_in','>=',start_date), ('sign_in','<=',end_date)]).mapped(lambda r: set(( datetime.datetime.strptime(r.sign_in, '%Y-%m-%d %H:%M:%S') if (r.sign_in!=False) else False, datetime.datetime.strptime(r.sign_out, '%Y-%m-%d %H:%M:%S') if (r.sign_out!=False) else False )));

        present_days = []
        for day in recs:
            day = [day_item for day_item in day if day_item != False]
            day.sort()
            '''
            [tuple(tuple(sign_in_date, sign_in_time), tuple(sign_out_date, sign_out_time)), ...]
            '''
            if len(day) == 2:
                present_days.append(tuple([tuple([day[0].date(),day[0].time()]), tuple([day[1].date(),day[1].time()])]))
            else:
                present_days.append(tuple([tuple([day[0].date(),day[0].time()]), False]))

        # Find the days for which the employee is absent
        leave_days = [];
        recs=self.env['hr.holidays'].search([('employee_id','=',employee_id), ('date_from','>=',start_date), ('date_to','<=',end_date), ('type','=','remove')]).mapped(lambda r: tuple(( datetime.datetime.strptime(r.date_from, '%Y-%m-%d %H:%M:%S').date() if (r.date_from!=False and r.state=="validate" and r.type=="remove") else False, datetime.datetime.strptime(r.date_to, '%Y-%m-%d %H:%M:%S').date() if (r.date_to!=False and r.state=="validate" and r.type=="remove") else False )));
        '''
        recs = [(datetime.date(2017, 5, 13), datetime.date(2017, 5, 13)), ...]
        '''
        for rec in recs:
            if not rec[0] or not rec[1]: continue;
            delta=rec[0]-rec[1];
            leave_days.extend([rec[0]+datetime.timedelta(days=day) for day in range(delta.days+1)]);

        '''
        Calculate all holidays including public holidays
        '''
        public_holidays = []
        public_holidays_recs = self.env['hr.holidays'].search([('employee_id','=',employee_id), ('date_from','>=',start_date), ('date_to','<=',end_date), ('type','=','remove'), ('holiday_status_id','=',5)])
        public_holidays_recs = public_holidays_recs.mapped(lambda r: tuple(( datetime.datetime.strptime(r.date_from, '%Y-%m-%d %H:%M:%S').date() if (r.date_from!=False and r.state=="validate" and r.type=="remove") else False, datetime.datetime.strptime(r.date_to, '%Y-%m-%d %H:%M:%S').date() if (r.date_to!=False and r.state=="validate" and r.type=="remove") else False )));
        for public_holidays_rec in public_holidays_recs:
            delta = public_holidays_rec[1]-public_holidays_rec[0];
            if delta != 0:
                public_holidays.extend([public_holidays_rec[0]+datetime.timedelta(days=day) for day in range(delta.days+1)])

        '''
        Calculate the attendance of the employee
        'P' marks the day for employee was present
        'A' marks the day for employee was absent
        'H' public holidays or paid leaves
        'D' marks the a normal day of the week (non working day)

        selected_days_with_attendance = [(datetime.date(2017, 5, 1),), (datetime.date(2017, 5, 2),), ...]
        '''
        selected_days_with_attendance=[(day, ) for day in selected_days]
        # attendance_days=[];
        for idx, day in enumerate(selected_days_with_attendance):
            # Check if day is sunday
            if day[0].isoweekday() in [7] or day[0] in public_holidays:
                selected_days_with_attendance[idx]+=("H",)
            # Check if selected day is in array of present days(sign in days)
            elif day[0] in [attendance_day[0][0] for attendance_day in present_days]:
                for attendance_day in present_days:
                    if day[0] == attendance_day[0][0]:
                        sign_in_time = (datetime.datetime.combine(attendance_day[0][0],attendance_day[0][1]) + datetime.timedelta(hours=5, minutes=30)).time()
                        sign_out_time = (datetime.datetime.combine(attendance_day[0][0],attendance_day[1][1]) + datetime.timedelta(hours=5, minutes=30)).time() if attendance_day[1] else ""
                        break

                selected_days_with_attendance[idx]+=("P", sign_in_time, sign_out_time,)
                # selected_days_with_attendance[idx]+=("P",)
            elif day[0] in leave_days:
                selected_days_with_attendance[idx]+=("A",)
            elif day[0] > datetime.datetime.now().date():
                selected_days_with_attendance[idx]+=("D",)
            else:
                selected_days_with_attendance[idx]+=("A",)

        return selected_days_with_attendance;

    @api.model
    def get_total_public_holidays(self, selected_days_with_attendance):
        public_holidays = [day[0] for day in selected_days_with_attendance if day[1]=="H"]
        total_public_holidays = len(public_holidays)
        return total_public_holidays

    @api.model
    def get_total_present_days1(self, selected_days_with_attendance,o,date):
        # print "selected ddayyyyyy", selected_days_with_attendance,o,date
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id),('sign_in','>=',date),('sign_out','<=',date)])
        # print "rec....................."  , rec
        if rec:
            return datetime.datetime.strptime(rec.sign_in, "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=5,minutes=30)
        else:
            return '---'

    @api.model
    def get_total_present_days(self, selected_days_with_attendance):
        present_days = [day[0] for day in selected_days_with_attendance if day[1]=="P"]
        total_present_days = len(present_days)
        total_public_holidays = self.get_total_public_holidays(selected_days_with_attendance)
        return total_present_days+total_public_holidays

    @api.model
    def get_total_leaves1(self, selected_days_with_attendance,o,date):
        rec = self.env['hiworth.hr.attendance'].search([('name','=',o.id),('sign_in','>=',date),('sign_out','<=',date)])
        # print "rec....................."  , rec
        if rec:
            return datetime.datetime.strptime(rec.sign_out, "%Y-%m-%d %H:%M:%S")+datetime.timedelta(hours=5,minutes=30)
        else:
            return '---'

    @api.model
    def get_total_leaves(self, selected_days_with_attendance):
        
        leave_days = [day[0] for day in selected_days_with_attendance if day[1]=="A"]
        total_leave_days = len(leave_days)
        return total_leave_days

# recs  [datetime.datetime(2017, 4, 1, 0, 0), datetime.datetime(2017, 4, 2, 0, 0), datetime.datetime(2017, 4, 3, 0, 0), datetime.datetime(2017, 4, 4, 0, 0), datetime.datetime(2017, 4, 5, 0, 0), datetime.datetime(2017, 4, 6, 0, 0), datetime.datetime(2017, 4, 7, 0, 0), datetime.datetime(2017, 4, 8, 0, 0), datetime.datetime(2017, 4, 9, 0, 0), datetime.datetime(2017, 4, 10, 0, 0), datetime.datetime(2017, 4, 11, 0, 0), datetime.datetime(2017, 4, 12, 0, 0), datetime.datetime(2017, 4, 13, 0, 0), datetime.datetime(2017, 4, 14, 0, 0), datetime.datetime(2017, 4, 15, 0, 0), datetime.datetime(2017, 4, 16, 0, 0), datetime.datetime(2017, 4, 17, 0, 0), datetime.datetime(2017, 4, 18, 0, 0), datetime.datetime(2017, 4, 19, 0, 0), datetime.datetime(2017, 4, 20, 0, 0), datetime.datetime(2017, 4, 21, 0, 0), datetime.datetime(2017, 4, 22, 0, 0), datetime.datetime(2017, 4, 23, 0, 0), datetime.datetime(2017, 4, 24, 0, 0), datetime.datetime(2017, 4, 25, 0, 0), datetime.datetime(2017, 4, 26, 0, 0), datetime.datetime(2017, 4, 27, 0, 0), datetime.datetime(2017, 4, 28, 0, 0), datetime.datetime(2017, 4, 29, 0, 0), datetime.datetime(2017, 4, 30, 0, 0)]
# recs  [datetime.date(2017, 4, 19), datetime.date(2017, 4, 17), datetime.date(2017, 4, 18), datetime.date(2017, 4, 10), datetime.date(2017, 4, 16)]
