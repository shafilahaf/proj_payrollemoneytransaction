from odoo import models, fields, api # type: ignore
from odoo.exceptions import UserError, ValidationError # type: ignore
import base64
import io
import xlrd
import time
from odoo.tools import mute_logger
import logging

_logger = logging.getLogger(__name__)
class PayrollConfig(models.TransientModel):
    _name = 'payroll.config.all'
    
    description = fields.Char(string="Description", default="Kebutuhan Config Internal", readonly=True)
    excel_file = fields.Binary(string="Upload Attendance Log File", attachment=True)

    def fix_status_approval_entries(self):
        time_off_req = self.env['payroll.time.off.request'].search([('status', '=', '5')])

        for request in time_off_req:
            approval_entries = self.env['payroll.approval.entries'].search([
                ('document_id', '=', request.id),
                ('status', '=', '2') 
            ])

            for entry in approval_entries:
                last_approved_entry = self.env['payroll.approval.entries'].search([
                    ('document_id', '=', request.id),
                    ('status', '=', '5')  # 'Approved'
                ], order='approved_date desc', limit=1)

                if last_approved_entry:
                    entry.status = '5'
                    entry.approved_by = last_approved_entry.approved_by
                    entry.approved_date = last_approved_entry.approved_date
                    entry.internal_note = f'Correcting pending approval entries {last_approved_entry.approved_by.name}'
                else:
                    entry.status = '5'
                    entry.approved_by = self.env.user.id
                    entry.approved_date = fields.Date.today()
                    entry.internal_note = 'Correcting pending approval entries by Admin'
                    # raise ValidationError(f'No approved entries found for request {request.name}.')
                
        return True

    def fix_source_id_attlog(self):
        attendance_log = self.env['payroll.attendance.log'].search([
            ('source', 'ilike', 'Time Off Request'),
            ('source_id', '!=', False)
        ])
        for log in attendance_log:
            try:
                source_id = int(log.source_id)
            except (ValueError, TypeError):
                continue

            approval_entries = self.env['payroll.approval.entries'].search([
                ('id', '=', source_id)
            ], limit=1)
            
            if approval_entries and approval_entries.document_id:
                log.source_id = approval_entries.document_id.id

    def fill_username_in_employee(self):
        employees = self.env['payroll.employees'].search([('username', '=', False)])
        for employee in employees:
            user = self.env['res.users'].search([('id', '=', employee.user_id.id)], limit=1)
            if user:
                employee.username = user.login


    def fill_employee_id_resusers(self):
        resusers = self.env['res.users'].search([('payroll_employee_id', '=', False)])
        for user in resusers:
            employee = self.env['payroll.employees'].search([('user_id', '=', user.id)], limit=1)
            if employee:
                user.payroll_employee_id = employee.id
                user.payroll_address = employee.address
                user.payroll_positions_level = employee.current_position.level
                user.payroll_address_2 = employee.address_2
                user.payroll_phone =  employee.phone
                user.payroll_email =  employee.email
                user.payroll_emergency_contact =  employee.emergency_contact
                user.payroll_emergency_phone =  employee.emergency_phone
                user.payroll_gender =  employee.gender
                user.payroll_date_of_birth =  employee.date_of_birth
                user.payroll_country_id =  employee.country_id
                user.payroll_city_id =  employee.city_id
                user.payroll_visa_number =  employee.visa_number
                user.payroll_visa_expire_date =  employee.visa_expire_date
                user.payroll_passport_number =  employee.passport_number
                user.payroll_passport_expire_date =  employee.passport_expire_date
                user.payroll_bank_id =  employee.bank_id
                user.payroll_bank_account_number =  employee.bank_account_number
                user.payroll_date_of_birth = employee.username

    def delete_all_attendance_logs(self):
        attendance_logs = self.env['payroll.attendance.log'].search([])
        attendance_logs.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def fill_employee_id_tor(self):
        time_off_requests = self.env['payroll.time.off.request'].search([('employee_id', '=', False)])
        if not time_off_requests:
            raise UserError('No Time Off Requests without Employee ID found.')
        
        for request in time_off_requests:
            employee = self.env['payroll.employees'].search([('user_id', '=', request.created_by.id)], limit=1)
            if employee:
                request.employee_id = employee.id
            else:
                _logger.warning(f"No matching employee found for user {request.created_by.name}")


    def import_attendance_log_from_excel(self):
        if not self.excel_file:
            raise UserError("Please upload an Excel file to import.")

        # Decode the file
        file_data = base64.b64decode(self.excel_file)
        file_stream = io.BytesIO(file_data)

        # Record the start time
        start_time = time.time()

        # Read the Excel file using xlrd
        try:
            workbook = xlrd.open_workbook(file_contents=file_stream.read())
            sheet = workbook.sheet_by_index(0)  # Assuming data is in the first sheet
        except Exception as e:
            raise UserError(f"Failed to read the Excel file: {str(e)}")

        # Validate columns (assuming the first row is the header)
        required_columns = [
            'Employee', 'Date', 'Start Time', 'End Time', 'Shift', 'Working Hours', 'Late', 
            'Source', 'Source ID', 'Manual', 'Late 2', 'Holiday Type', 'Time Off Type', 'Weekday', 
            'Holiday', 'Late Minutes', 'Night Differential', 'PH Point', 'OT Hours', 'OT Point', 
            'Late 3', 'Late 4', 'NIK', 'Department', 'Status'
        ]

        header = [cell.value for cell in sheet.row(0)]
        if not all(column in header for column in required_columns):
            raise ValidationError("The Excel file does not contain the required columns.")

        # Initialize counters
        import_count = 0
        error_count = 0

        # Iterate over the rows and create attendance logs
        for row_idx in range(1, sheet.nrows):
            row = dict(zip(header, sheet.row_values(row_idx)))
            try:
                employee_id = self.env['payroll.employees'].search([('nik', '=', row['NIK'])], limit=1).id

                shift_id = False
                if row['Shift']:
                    shift_id = self.env['payroll.shifts'].search([('name', '=', row['Shift'])], limit=1).id

                holiday_id = False
                if row['Holiday']:
                    holiday_id = self.env['payroll.holiday'].search([('name', '=', row['Holiday'])], limit=1).id

                department_id = False
                if row['Department']:
                    department_id = self.env['payroll.device.department'].search([('name', '=', row['Department'])], limit=1).id

                # Find the selection value based on the label from the Excel file
                time_off_type_value = dict((v, k) for k, v in self.env['payroll.attendance.log']._fields['time_off_type'].selection).get(row['Time Off Type'], '')

                self.env['payroll.attendance.log'].create({
                    'employee_id': employee_id,
                    'date': xlrd.xldate.xldate_as_datetime(row['Date'], workbook.datemode).date(),
                    'start_time': xlrd.xldate.xldate_as_datetime(row['Start Time'], workbook.datemode),
                    'end_time': xlrd.xldate.xldate_as_datetime(row['End Time'], workbook.datemode),
                    'shift_id': shift_id,
                    'working_hours': row['Working Hours'],
                    'is_latelog': bool(row['Late']),
                    'source': row['Source'],
                    'source_id': row['Source ID'],
                    'is_manual': bool(row['Manual']),
                    'is_late_2': bool(row['Late 2']),
                    'weekday': int(row['Weekday']),
                    'holiday': holiday_id,
                    'late_minutes': row['Late Minutes'],
                    'is_night_diff': bool(row['Night Differential']),
                    'ph_points': row['PH Point'],
                    'ot_hours': row['OT Hours'],
                    'ot_points': row['OT Point'],
                    'is_late_3': bool(row['Late 3']),
                    'is_late_4': bool(row['Late 4']),
                    'nik': row['NIK'],
                    'department_id': department_id,
                    'status': row['Status'],
                    'holiday_type': row['Holiday Type'],
                    'time_off_type': time_off_type_value,  # Use the value corresponding to the label
                })

                import_count += 1
            except Exception as e:
                error_count += 1

        # Record the end time and calculate the duration
        end_time = time.time()
        duration = end_time - start_time
        
        # Return the wizard with the result message
        _logger.info(f"Import complete!\nSuccessfully imported {import_count} records.\nFailed to import {error_count} records.\nTime taken: {duration:.2f} seconds.")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Attendance Log Import',
                'message': f"Import complete!\nSuccessfully imported {import_count} records.\nFailed to import {error_count} records.\nTime taken: {duration:.2f} seconds.",
                'sticky': False
            }
        }
    