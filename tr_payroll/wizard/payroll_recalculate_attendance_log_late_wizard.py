from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta, time
import pytz

class PayrollRecalculateAttendanceLogLateWizard(models.TransientModel):
    _name = 'payroll.recalculate.attendance.log.late.wizard'
    _description = 'Payroll Recalculate Attendance Log - Late Wizard'

    calculate_from_date = fields.Date(string='Calculate From Date', required=True)

    def calculate(self):
        """
        Recalculate Attendance Log Late logic similar to fnProcessCheckin
        """
        self.ensure_one()

        calculate_from_date = self.calculate_from_date
        total_rec = 0

        if not calculate_from_date:
            raise ValidationError('Please input Calculate From Date!')

        calcdate = fields.Date.from_string(calculate_from_date)

        attendance_logs = self.env['payroll.attendance.log'].search([
            ('date', '>=', calcdate),
            ('shift_id', '!=', False)
        ])

        for att_log in attendance_logs.with_progress(msg="Processing"):
            total_rec += 1

            # Reset late flags and late minutes
            att_log.write({
                'is_latelog': False,
                'is_late_2': False,
                'is_late_3': False,
                'is_late_4': False,
                'late_minutes': 0
            })

            employee = self.env['payroll.employees'].search([('id', '=', att_log.employee_id.id)])
            shift = self.env['payroll.shifts'].search([('id', '=', att_log.shift_id.id)])

            if shift:
                att_log.write({
                    'shift_id': shift.id,
                    'is_night_diff': shift.is_night_diff
                })

                # Calculate shift start time
                shift_start_hours = int(shift.start_time)
                shift_start_minutes = int((shift.start_time - shift_start_hours) * 60)
                shift_start_time = time(shift_start_hours, shift_start_minutes)

                # Localize shift start time
                jammasuk = datetime.combine(att_log.date, shift_start_time)
                local_tz = pytz.timezone('Asia/Jakarta')  # GMT+7 timezone
                jammasuk_local = local_tz.localize(jammasuk)

                # Convert att_log.start_time to GMT+7
                if att_log.start_time:
                    start_time_utc = pytz.utc.localize(att_log.start_time)
                    start_time_local = start_time_utc.astimezone(local_tz)

                    if start_time_local > jammasuk_local:
                        # Calculate late minutes
                        late_minutes = (start_time_local - jammasuk_local).total_seconds() / 60
                        att_log.write({'late_minutes': late_minutes})

                        # Check late tolerance based on employee position
                        emp_position = employee.current_position

                        if emp_position.late_tolerance > 0:
                            late = late_2 = late_3 = late_4 = False

                            late = self.check_late_tolerance(emp_position.late_tolerance, jammasuk_local, start_time_local)
                            late_2 = self.check_late_tolerance(emp_position.late_tolerance_2, jammasuk_local, start_time_local)
                            late_3 = self.check_late_tolerance(emp_position.late_tolerance_3, jammasuk_local, start_time_local)
                            late_4 = self.check_late_tolerance(emp_position.late_tolerance_4, jammasuk_local, start_time_local)

                            # Update late flags in the attendance log
                            att_log.write({
                                'is_latelog': late,
                                'is_late_2': late_2,
                                'is_late_3': late_3,
                                'is_late_4': late_4
                            })

            if not att_log.time_off_type:
                att_log.write({'PH_point': 1})

        message = f"Recalculate Attendance Log Late Success! Total Record: {total_rec}"
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success!',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def check_late_tolerance(self, tolerance_minutes, shift_start, punch_time):
        """Check if the punch time exceeds the late tolerance."""
        if tolerance_minutes is not None and tolerance_minutes > 0:
            tolerance = timedelta(minutes=tolerance_minutes)
            return punch_time > (shift_start + tolerance)
        return False
