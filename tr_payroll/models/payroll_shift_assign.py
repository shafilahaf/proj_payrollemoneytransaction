from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import openpyxl
import base64
from io import BytesIO

# Variabel Set Selections Fields --START
setSelectionStatus = [
    ("1", "Draft"),
    ("2", "Pending"),
    ("3", "Processed"),
    ("4", "Cancelled"),
]
setSelectionMonth = [
    ("1", "Januari"),
    ("2", "Februari"),
    ("3", "Maret"),
    ("4", "April"),
    ("5", "Mei"),
    ("6", "Juni"),
    ("7", "Juli"),
    ("8", "Agustus"),
    ("9", "September"),
    ("10", "Oktober"),
    ("11", "November"),
    ("12", "Desember"),
]
# Variabel Set Selections Fields --END

class PayrollShiftAssignHeader(models.Model):
    _name = "payroll.shift.assign.header"
    _description = "Payroll Shift Assign Header"
    _rec_name = "name"

    name = fields.Char(
        string="Name",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: ("New"),
    )
    assign_date = fields.Date(
        string="Assign Date", default=fields.Date.context_today, readonly=True
    )
    assign_by_id = fields.Many2one(
        "res.users",
        string="Assign User",
        default=lambda self: self.env.user,
        readonly=True,
    )
    status = fields.Selection(
        setSelectionStatus, string="Status", default="1", required=True
    )
    month = fields.Selection(
        setSelectionMonth, string="Month", required=True
    )
    year = fields.Char(string="Year", required=True)

    # Shift Assign Details
    shift_assign_detail_ids = fields.One2many(
        "payroll.shift.assign.details",
        "shift_assign_ids",
        string="Shift Assign Details",
    )

    category_id = fields.Many2one(
        "payroll.employee.categories", string="Category", compute="_compute_category", store=True
    )
    department_id = fields.Many2one(
        "payroll.device.department", string="Department", compute="_compute_department", store=True
    )

    @api.depends('assign_by_id')
    def _compute_category(self):
        for record in self:
            employee = self.env['payroll.employees'].search([
                ('user_id', '=', record.assign_by_id.id)
            ], limit=1)
            record.category_id = employee.category_id if employee else False

    @api.depends('assign_by_id')
    def _compute_department(self):
        for record in self:
            employee = self.env['payroll.employees'].search([
                ('user_id', '=', record.assign_by_id.id)
            ], limit=1)
            record.department_id = employee.department_id if employee else False

    def action_import_excel(self):
        """
        This method will open a new window to import excel file."""
        return {
            "name": ("Import Excel"),
            "view_mode": ("form"),
            "res_model": ("payroll.shifts.assign.import.excel.wizard"),
            "type": ("ir.actions.act_window"),
            "target": ("new"),
        }
    

    def assign_to_employee(self):
        """
        This method will assign the shift to the employee."""
        # Check details
        process = 1
        payroll_employee_shift = self.env['payroll.employee.shift']
        for detail in self.shift_assign_detail_ids:
            # Delete all records in payroll.employee.shift
            payroll_employee_shift.search([('employee_id', '=', detail.employee_id.id), ('start_date', '=', detail.start_date)]).unlink()
            if detail.status not in ["OFF", "LEAVE", "P", "SL", "DE"]:
                if detail.status != "PASS":
                    process = 0

        if process == 1:
            for detail in self.shift_assign_detail_ids.with_progress(msg="Processing"):
                if detail.status == "PASS":
                    # Create a new record in payroll.employee.shift
                    payroll_employee_shift.create(
                        {
                            "employee_id": detail.employee_id.id,
                            "shifts_id": detail.shift_id.id,
                            "start_date": detail.start_date,
                            "end_date": detail.end_date,
                            "companies_id": detail.companies_id.id,
                            "shift_assign_id" : self.id
                        }
                    )

                else:
                    workhour = 0
                    if detail.status == "OFF":
                        typeofftime = "4"
                        workhour = 0
                    elif detail.status == "LEAVE":
                        typeofftime = "1"
                        workhour = 0
                    elif detail.status == "SL":
                        typeofftime = "2"
                        workhour = 0
                    elif detail.status == "P":
                        typeofftime = "3"
                        workhour = 0
                    elif detail.status == "DE":
                        typeofftime = "5"
                        workhour = 12
                    attendancelogcheck = self.env['payroll.attendance.log'].search([
                        ('employee_id', '=', detail.employee_id.id),
                        ('date', '=', detail.start_date),
                        ('time_off_type', '=', typeofftime)
                    ])
                    if not attendancelogcheck:
                        attnewlog =  self.env['payroll.attendance.log'].create({
                            'employee_id': detail.employee_id.id,
                            'date': detail.start_date,
                            'start_time': detail.start_date,
                            'end_time': detail.start_date,
                            'shift_id': detail.shift_id.id,
                            'working_hours': workhour,
                            'time_off_type': typeofftime,
                            'source': "Import Shift Assign",
                            'source_id': detail.id,
                            'nik': detail.employee_id.nik,
                            'department_id': detail.employee_id.department_id.id,
                        })

                        
                        holidaycheck = self.env['payroll.holiday'].search([
                            ('day', '=', detail.start_date.day),
                            ('month', '=', str(detail.start_date.month)),
                        ], limit=1)
                        if holidaycheck:
                            attnewlog.holiday = holidaycheck.id
                            attnewlog.holiday_type = holidaycheck.type
                      
                        if typeofftime == "1":
                            emp = self.env['payroll.employees'].search([('id', '=', detail.employee_id.id)])
                            if emp:
                                if emp.active_leave_date == False or emp.active_leave_date < detail.start_date:
                                    emp.write({
                                        'active_leave_date': detail.start_date
                                    })

                                empdet = self.env['payroll.employee.details'].search([
                                    ('employee_id','=',detail.employee_id.id),
                                    ('type_id','=','1')
                                ])

                                for ed in empdet :
                                    ed.last_leave_date = detail.start_date
                
            assshift = self.env['payroll.shift.assign.header'].search([('id', '=', self.id)])
            assshift.status = '3'

            self.FnCheckShiftonAttendance()
        else:
            raise UserError("Please check the status of the employee.")

            
    def FnCheckShiftonAttendance(self) :
        empshift = self.env['payroll.employee.shift'].search([
            ('shift_assign_id','=',self.id)
        ])

        for es in empshift :
            attendancelogcheck = self.env['payroll.attendance.log'].search([
                ('employee_id', '=', es.employee_id.id),
                ('date', 'in', [es.start_date,es.end_date])
            ])

            for attlog in attendancelogcheck :
                attlog.shift_id = es.shifts_id.id
                attlog.is_night_diff = es.shifts_id.is_night_diff

                shift_start_hours = int(es.shifts_id.start_time)
                shift_start_minutes = int((es.shifts_id.start_time - shift_start_hours) * 60)
                #jammasuk = Datetime(att.StartTime.Year, att.StartTime.Month, att.StartTime.Day, shift.StartTime.Hours, shift.StartTime.Minutes, shift.StartTime.Seconds);      
                jammasuk = datetime(attlog.start_time.year,attlog.start_time.month,attlog.start_time.day,shift_start_hours,shift_start_minutes,0)

                late_minutes = 0
                late= False
                late_2= False
                late_3= False
                late_4= False
                attlog.is_latelog = False
                attlog.is_late_2 = False
                attlog.is_late_3 = False
                attlog.is_late_4 = False

                start_time_plus_7 = attlog.start_time + timedelta(hours=7)
            
                if start_time_plus_7 > jammasuk:
                    late_minutes = start_time_plus_7  - jammasuk
                    late_minutes = late_minutes.total_seconds() / 60
                    attlog.late_minutes =  late_minutes

                def check_late_tolerance(tolerance):
                    if tolerance:
                        tolerance_time = jammasuk + timedelta(minutes=tolerance)
                        return start_time_plus_7 >= tolerance_time
                    return False

                emp_position = attlog.employee_id.current_position

                if late_minutes > 0:
                    if emp_position.late_tolerance and check_late_tolerance(emp_position.late_tolerance):
                        late = True
                    elif emp_position.late_tolerance_2 and check_late_tolerance(emp_position.late_tolerance_2):
                        late_2 = True
                    elif emp_position.late_tolerance_3 and check_late_tolerance(emp_position.late_tolerance_3):
                        late_3 = True
                    elif emp_position.late_tolerance_4 and check_late_tolerance(emp_position.late_tolerance_4):
                        late_4 = True

                    attlog.is_latelog = late
                    attlog.is_late_2 = late_2
                    attlog.is_late_3 = late_3
                    attlog.is_late_4 = late_4


                attlog_date = attlog.date
                day = attlog_date.day
                month = attlog_date.month

                holiday = self.env['payroll.holiday'].search([
                    ('day', '=', day),
                    ('month', '=', month),       
                ], limit=1)

                if holiday:
                    attlog.holiday_type = holiday.type



    def cancel_shift_assign(self):
        """
        This method will cancel the shift assign."""
        # # Delete all records in payroll.employee.shift
        # payroll_employee_shift = self.env['payroll.employee.shift']
        # for detail in self.shift_assign_detail_ids:
        #     payroll_employee_shift.search([('employee_id', '=', detail.employee_id.id)]).unlink()
        self.status = '4'
       

    @api.model
    def create(self, vals):
        """
        This method will generate a new sequence for the record."""
        if vals.get("name", ("New")) == ("New"):
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "payroll.shift.assign.header"
            ) or ("New")
        return super(PayrollShiftAssignHeader, self).create(vals)


class PayrollShiftAssignDetails(models.Model):
    _name = "payroll.shift.assign.details"
    _description = "Payroll Shift Assign Details"

    # Shift Assign Details
    shift_assign_ids = fields.Many2one(
        "payroll.shift.assign.header", string="Shift Assign Header"
    )

    employee_id = fields.Many2one("payroll.employees", string="Employee", required=True)
    department_id = fields.Many2one(
        "payroll.device.department", string="Device Department", required=True
    )
    shift_id = fields.Many2one("payroll.shifts", string="Shift")
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    companies_id = fields.Many2one("payroll.companies", string="Company", required=True)
    status = fields.Char(string="Status")


