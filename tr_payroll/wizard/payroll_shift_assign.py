from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
import openpyxl
import base64
from io import BytesIO
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)
class PayrollShiftsAssignImportExcelWizard(models.TransientModel):
    _name = "payroll.shifts.assign.import.excel.wizard"
    _description = "Payroll Shifts Assign Import Excel Wizard"

    excel_file = fields.Binary(string="Excel File", required=True)

    def import_excel(self):
        try:
            excel_file = base64.b64decode(self.excel_file)
            workbook = openpyxl.load_workbook(BytesIO(excel_file))
            worksheet = workbook.active
        
            # Skip first two rows (header and subheader)
            rows = list(worksheet.iter_rows(values_only=True))
            header = rows[2]
            data_rows = rows[3:]

            # Get the active record to extract month and year
            active_record = self.env['payroll.shift.assign.header'].browse(self._context.get('active_id'))
            month = int(active_record.month)
            year = int(active_record.year)
            
            # Calculate the start date of the month
            base_date = datetime(year, month, 1)

            for row in data_rows:
                # Extract data from row
                name, nik, location, *shifts = row

                # Find employee by NIK
                employee = self.env["payroll.employees"].search([
                    ("nik", "=", str(nik)),
                    ("department_id", "=", location)  # Menambahkan filter berdasarkan department_id
                ], limit=1)

                if not employee:
                    # raise UserError(f"Employee with NIK {nik} not found")
                    continue
                
                for i, shift_name in enumerate(shifts):
                    if shift_name:
                        # Calculate the start_date and end_date
                        start_date = base_date + timedelta(days=i)
                        end_date = start_date

                        # Get all shift list
                        shift = self.env["payroll.shifts"].search([])
                        shift = shift.filtered(lambda s: s.name == str(shift_name))
                        _logger.info(f"shift_name: {shift_name}")
                        
                        shift_assign_status = ""
                        if shift:
                            shift_assign_status = "PASS"
                        # else:
                        #     shift_assign_status = f"FAIL: Shift {shift_name} not found"

                        if shift:
                            self.env["payroll.shift.assign.details"].create({
                                "shift_assign_ids": self._context.get("active_id"),
                                "employee_id": employee.id,
                                "shift_id": self.env["payroll.shifts"].search([("name", "=", str(shift_name))]).id,
                                "department_id": employee.department_id.id,
                                "companies_id": employee.company_id.id,
                                "start_date": start_date,
                                "end_date": end_date,
                                "status": shift_assign_status,
                            })
                        # shift id
                        _logger.info(f"shift_id: {shift.id}")

                        if shift_name.upper() in ["OFF", "LEAVE", "P", "SL", "DE"]:
                            self.env["payroll.shift.assign.details"].create({
                                    "shift_assign_ids": self._context.get("active_id"),
                                    "employee_id": employee.id,
                                    "department_id": employee.department_id.id,
                                    "companies_id": employee.company_id.id,
                                    "status": shift_name.upper(),
                                    "shift_id": self.env["payroll.shifts"].search([], limit=1).id, #default data
                                    "start_date": start_date,
                                    "end_date": end_date,
                            })
                        # status in header set to pending
                        active_record.status = '2'
        except Exception as e:
            raise UserError(f"Failed to import Excel file: {e}")
        return {
            "type": "ir.actions.act_window",
            "res_model": "payroll.shift.assign.header",
            "view_mode": "form",
            "res_id": self._context.get("active_id"),
            "target": "current",
        }