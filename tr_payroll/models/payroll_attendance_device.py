from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging
import pytz

_logger = logging.getLogger(__name__)

class PayrollAttendanceDevice(models.Model):
    _name = 'payroll.attendance.device'
    _description = 'Attendance Device'

    # employee_id = fields.Many2one('payroll.employees', string='Employee', required=True)
    nik = fields.Char(string='NIK')
    punch_type = fields.Selection([('0', 'Check In'),
                                   ('1', 'Check Out'),
                                   ('2', 'Break Out'),
                                   ('3', 'Break In'),
                                   ('4', 'Overtime In'),
                                   ('5', 'Overtime Out')],
                                  string='Punching Type')
    
    punching_time = fields.Datetime(string='Punching Time')
    is_processed = fields.Boolean(string='Is Processed', default=False)
    department = fields.Char(string = 'Deparment')
   
    punch_date = fields.Date(string="Punch Date", compute='_compute_punch_date', store=True)
    punch_time = fields.Float(string="Punch Time", compute='_compute_punch_time', store=True)
    punching_time_2 = fields.Char(string='Punching Time 2', compute='_compute_punching_time_2', store=True)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        user_groups = user.groups_id

        allowed_departments = []

        for group in user_groups:
            if group.is_active:
                allowed_departments += group.department_ids.ids

        domain = [] 
        
        # Domain only department that user allowed
        if allowed_departments:
            department_name = self.env['payroll.device.department'].search([('id', 'in', allowed_departments)])
            domain = [('department', 'in', department_name.mapped('name'))]

        if domain:
            args += domain

        return super(PayrollAttendanceDevice, self).search(args, offset, limit, order, count=count)

    @api.depends('punching_time')
    def _compute_punch_date(self):
        local_tz = pytz.timezone('Asia/Jakarta')  # Replace with your local timezone
        for record in self:
            if record.punching_time:
                # Convert punching_time to local timezone
                utc_time = fields.Datetime.from_string(record.punching_time).replace(tzinfo=pytz.utc)
                local_time = utc_time.astimezone(local_tz)
                # Set the punch_date
                record.punch_date = local_time.date()
            else:
                record.punch_date = False
                
    @api.depends('punching_time')
    def _compute_punch_time(self):
        local_tz = pytz.timezone('Asia/Jakarta')  # Replace with your local timezone
        for record in self:
            if record.punching_time:
                # Convert punching_time to local timezone
                utc_time = fields.Datetime.from_string(record.punching_time).replace(tzinfo=pytz.utc)
                local_time = utc_time.astimezone(local_tz)
                # Extract the time part
                record.punch_time = local_time.hour + local_time.minute / 60
            else:
                record.punch_time = 0
                
    @api.depends('punch_date', 'punch_time')
    def _compute_punching_time_2(self):
        for record in self:
            if record.punch_date and record.punch_time:
                # Combine punch_date and punch_time into a single Datetime
                punch_date_time = datetime.strptime(str(record.punch_date), '%Y-%m-%d')
                punch_time_hours = int(record.punch_time)
                punch_time_minutes = int((record.punch_time - punch_time_hours) * 100)
                punch_datetime = punch_date_time + timedelta(hours=punch_time_hours, minutes=punch_time_minutes)
                record.punching_time_2 = punch_datetime
            else:
                record.punching_time_2 = False

    @api.model
    def create(self, vals):
        res = super(PayrollAttendanceDevice, self).create(vals)
        #res.process_attendance_log()
        #res.batch_update_att_log()
        return res

    def process_attendance_log(self, department, start_date=None, end_date=None):
        self.fnProcessCheckin(department, start_date, end_date)
        self.fnProcessCheckOut(department, start_date, end_date)

    def fnCheckEmployeeData(self,nik,deptId) :
        emp_data = self.env['payroll.employees'].search([('nik', '=', nik), ('department_id', '=', deptId)], limit=1) 
        if not emp_data:
            new_employee_setup = self.env['payroll.scheduler.setup'].search([], limit=1)
            employee = self.env['payroll.employees'].create({
                'name': nik,
                'nik': nik,
                'department_id': deptId,
                'company_id': new_employee_setup.default_company_employee.id,
                'active_date': fields.Date.today(),
                'working_status': '1',
                'contract_id': new_employee_setup.default_contract_employee.id,
                'current_website': new_employee_setup.default_website_employee.id,
                'category_id': new_employee_setup.default_category_employee.id,
                'current_position': new_employee_setup.default_position_employee.id,
            })
            return employee
        else : 
            return emp_data

    def fnGetShift(self,attd,empId) :
        #shift_model = self.env['payroll.shifts']
        employee_shift = self.env['payroll.employee.shift'].search([
            ('employee_id', '=', empId),
            ('start_date', '<=', attd.punch_date),
            ('end_date', '>=', attd.punch_date)], limit=1)\
            
        return employee_shift
    
    def fnProcessCheckin(self,department,start_date,end_date) :
        if not department:
            att_device = self.env['payroll.attendance.device'].search([
                ('is_processed','=',False),
                ('punch_type','in', ['0','4']),
            ],order = "punching_time asc")
        elif start_date and end_date:
            att_device = self.env['payroll.attendance.device'].search([
                ('is_processed','=',False),
                ('punch_type','in', ['0','4']),
                ('department', '=', department),
                ('punch_date', '>=', start_date),
                ('punch_date', '<=', end_date)
            ],order = "punching_time asc")
        else:
            att_device = self.env['payroll.attendance.device'].search([
                ('is_processed','=',False),
                ('punch_type','in', ['0','4']),
                ('department', '=', department),
            ],order = "punching_time asc")

        if att_device:
            for attd in att_device.web_progress_iter(att_device, msg="Processing"):
                # attd.web_progress_iter(attd, msg="Message Test")
                dept = self.env['payroll.device.department'].search([
                        ('name','=',attd.department)
                    ])
                
                if dept :
                    #Check employee data
                    emp_data = self.fnCheckEmployeeData(attd.nik,dept.id)

                    PayrollAttendanceLog = self.env['payroll.attendance.log']

                    #get shift
                    employee_shift = self.fnGetShift(attd,emp_data.id)
                    
                    if attd.punch_type in ['0', '4']:  # Check In or Overtime In
                        # Check if an attendance log already exists for the employee on the same day
                        att_log = PayrollAttendanceLog.search([
                            ('employee_id', '=', emp_data.id),
                            ('date', '=', attd.punch_date)
                        ], limit=1)

                        if att_log.id == False:
                            shift_start_hours = int(employee_shift.shifts_id.start_time)
                            shift_start_minutes = int((employee_shift.shifts_id.start_time - shift_start_hours) * 60)
                            shift_start_time = timedelta(hours=shift_start_hours, minutes=shift_start_minutes)

                            utc = pytz.UTC
                            gmt_plus_7 = pytz.timezone('Asia/Bangkok')
                            punch_time_utc = utc.localize(attd.punching_time)
                            punch_time_dt = punch_time_utc.astimezone(gmt_plus_7)
                            
                            shift_start_dt = gmt_plus_7.localize(datetime(
                                                punch_time_dt.year, 
                                                punch_time_dt.month, 
                                                punch_time_dt.day, 
                                                shift_start_hours, 
                                                shift_start_minutes
                                            ))

                            hours = punch_time_dt.hour
                            minutes = punch_time_dt.minute
                            punch_time = timedelta(hours=hours, minutes=minutes)

                            late_minutes = 0
                            late= False
                            late_2= False
                            late_3= False
                            late_4= False
                            holiday= False
                            holiday_type = False

                            def check_late_tolerance(tolerance, shift_start_time, punch_time_dt):
                                if tolerance:
                                    tolerance_time = shift_start_time + timedelta(minutes=tolerance)
                                    return punch_time_dt >= tolerance_time
                                return False

                            emp_position = emp_data.current_position

                            if punch_time_dt > shift_start_dt:
                                late_minutes = (punch_time_dt - shift_start_dt).total_seconds() / 60

                                if emp_position.late_tolerance and check_late_tolerance(emp_position.late_tolerance, shift_start_dt, punch_time_dt):
                                    tolerance_time = shift_start_dt + timedelta(minutes=emp_position.late_tolerance)
                                    # late_minutes = (punch_time_dt - tolerance_time).total_seconds() / 60
                                    late_minutes = (punch_time_dt - shift_start_dt).total_seconds() / 60
                                else:
                                    late_minutes = (punch_time_dt - shift_start_dt).total_seconds() / 60

                                late = check_late_tolerance(emp_position.late_tolerance, shift_start_dt, punch_time_dt)
                                late_2 = check_late_tolerance(emp_position.late_tolerance_2, shift_start_dt, punch_time_dt)
                                late_3 = check_late_tolerance(emp_position.late_tolerance_3, shift_start_dt, punch_time_dt)
                                late_4 = check_late_tolerance(emp_position.late_tolerance_4, shift_start_dt, punch_time_dt)
                            else:
                                late_minutes = 0
                                late = late_2 = late_3 = late_4 = False

                            punch_date = attd.punch_date
                            day = punch_date.day
                            month = punch_date.month


                            holiday = self.env['payroll.holiday'].search([
                                ('day', '=', day),
                                ('month', '=', month),
                            ], limit=1)

                            if holiday:
                                holiday_type = holiday.type

                            if not att_log.time_off_type:
                                ph_point = 1

                            # Create the attendance log with the latest check-in

                            if not (late or late_2 or late_3 or late_4):
                                late_minutes = False
                           
                            self.env['payroll.attendance.log'].create({
                                'employee_id': emp_data.id,
                                'start_time': attd.punching_time,
                                'end_time': False,
                                'shift_id': employee_shift.shifts_id.id if employee_shift else False,
                                'nik': attd.nik,
                                'department_id': dept.id,
                                'date': attd.punch_date,
                                'is_latelog': late,
                                'is_late_2': late_2,
                                'is_late_3': late_3,
                                'is_late_4': late_4,
                                'weekday': attd.punch_date.weekday(),
                                'is_night_diff': employee_shift.shifts_id.is_night_diff if employee_shift else False,
                                'late_minutes': late_minutes,
                                'holiday': holiday.id if holiday else False,
                                'holiday_type': holiday_type if holiday else False,
                                'time_off_type': False,
                                'PH_point': ph_point,
                            })
                        attd.is_processed = True


    def fnProcessCheckOut(self,department,start_date, end_date) :
      
        # if not department:
        #     att_device = self.env['payroll.attendance.device'].search([
        #         ('is_processed','=',False),
        #         ('punch_type','in', ['1','5']),
        #         ('punch_date', '>=', start_date),
        #         ('punch_date', '<=', end_date),
        #     ],order = "punching_time asc")
        # else:
        #     att_device = self.env['payroll.attendance.device'].search([
        #         ('is_processed','=',False),
        #         ('punch_type','in', ['1','5']),
        #         ('department', '=', department),
        #         ('punch_date', '>=', start_date),
        #         ('punch_date', '<=', end_date)
        #     ],order = "punching_time asc")

        if not department:
            att_device = self.env['payroll.attendance.device'].search([
                ('is_processed','=',False),
                ('punch_type','in', ['1','5'])
            ],order = "punching_time asc")
        elif start_date and end_date:
            att_device = self.env['payroll.attendance.device'].search([
                ('is_processed','=',False),
                ('punch_type','in', ['1','5']),
                ('department', '=', department),
                ('punch_date', '>=', start_date),
                ('punch_date', '<=', end_date)
            ],order = "punching_time asc")
        else:
            att_device = self.env['payroll.attendance.device'].search([
                ('is_processed','=',False),
                ('punch_type','in', ['1','5']),
                ('department', '=', department)
            ],order = "punching_time asc")

        if att_device:
            for attd in att_device:
                dept = self.env['payroll.device.department'].search([
                        ('name','=',attd.department)
                    ])
                
                if dept :
                    #Check employee data
                    emp_data = self.fnCheckEmployeeData(attd.nik,dept.id)

                    PayrollAttendanceLog = self.env['payroll.attendance.log']
                        
                    if attd.punch_type in ['1', '5']:  # Check Out or Overtime Out
                        # Search for the latest attendance log covering the punch date and the previous day
                        attendance_log = PayrollAttendanceLog.search([
                            ('employee_id', '=', emp_data.id),
                            ('date', 'in', [attd.punch_date, attd.punch_date - timedelta(days=1)]),
                            ('time_off_type', '=', False),
                            ('start_time','<', attd.punching_time)
                        ], limit=1, order='date desc')  # Get the latest entry

                        if attendance_log:
                            punch_out_datetime = fields.Datetime.from_string(attd.punching_time)

                            # Calculate total working hours
                            working_hours = (punch_out_datetime - attendance_log.start_time).total_seconds() / 3600.0

                            # Calculate overtime hours (assuming 8 hours of regular work)
                            overtime_hours = max(0, working_hours - 8)

                            # Update the attendance log with the check-out time and overtime hours
                            attendance_log.write({
                                'end_time': punch_out_datetime,
                                'ot_hours': overtime_hours,
                            })

                            # OT points based on holiday type
                            if attendance_log.holiday_type == '2':
                                attendance_log.ot_points += 2
                            elif attendance_log.holiday_type == '1':
                                attendance_log.ot_points += 1

                            # Mark attendance as processed
                            attd.write({'is_processed': True})