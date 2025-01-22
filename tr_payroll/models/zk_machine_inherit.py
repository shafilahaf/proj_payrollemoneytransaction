from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from zk import ZK, const
import datetime
import pytz
from datetime import datetime, timedelta
import logging
import socket

_logger = logging.getLogger(__name__)
class PayrollZKMachineInherit(models.Model):
    _inherit = 'zk.machine'

    device_department_id = fields.Many2one('payroll.device.department', string='Department')
    last_date_run =  fields.Datetime('Last Date Run')

    def convert_att_log(self, start_date=None, end_date=None):
        attd = self.env['payroll.attendance.device']
        if start_date and end_date:
            _logger.info(f"Processing attendance logs for department '{self.device_department_id.name}' from {start_date} to {end_date}")
            attd.process_attendance_log(self.device_department_id.name, start_date, end_date)
        else:
            _logger.info(f"Processing all attendance logs for department '{self.device_department_id.name}' without date filter")
            attd.process_attendance_log(self.device_department_id.name)

    def scheduled_convert_att_log(self):
        machines = self.search([])
        for machine in machines:
            machine.convert_att_log()
            _logger.info(f"Completed scheduled convert_att_log for machine: {machine.name}")
    

    def test_connection(self):
        """Test the connection to the specified IP and port."""
        ip = self.name
        port = self.port_no
        timeout = 5

        try:
            with socket.create_connection((ip, port), timeout) as s:
                s.close()
            raise UserError("Connection to the device at IP {} and Port {} was successful.".format(ip, port))
        except (socket.timeout, socket.error) as e:
            raise UserError("Failed to connect to the device at IP {} and Port {}. Error: {}".format(ip, port, str(e)))
        
    def download_attendance_2(self):
        zk_attendance = self.env['zk.machine.attendance']
        att_obj = self.env['hr.attendance']
        payroll_attendance_device = self.env['payroll.attendance.device']
        
        for info in self:
            # Define the time zone as GMT+7
            gmt_plus_7_tz = pytz.timezone('Asia/Bangkok')  # GMT+7 timezone

            # Ensure that `last_date_run` is treated as GMT+7 time
            if info.last_date_run:
                # If `last_date_run` exists, ensure it's in GMT+7
                from_date = info.last_date_run.astimezone(gmt_plus_7_tz)
            else:
                # Default to 1 day before now in GMT+7
                from_date = datetime.now(gmt_plus_7_tz) - timedelta(days=1)

            # Set `to_date` to the current time in GMT+7
            to_date = datetime.now(gmt_plus_7_tz)

            machine_ip = info.name
            zk_port = info.port_no
            timeout = 15
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=timeout, password=0, force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))
            
            conn = self.device_connect(zk)
            if conn:
                try:
                    user = conn.get_users()
                except:
                    user = False

                try:
                    # Fetch all attendance records
                    attendance = conn.get_attendance()
                except:
                    attendance = False

                if attendance:
                    for each in attendance:
                        atten_time = each.timestamp
                        # Convert `atten_time` to timezone-aware datetime
                        atten_time = pytz.utc.localize(datetime.strptime(atten_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S'))

                        # Convert `atten_time` from UTC to GMT+7
                        atten_time = atten_time.astimezone(gmt_plus_7_tz)

                        # Apply filtering manually for attendance records within the date range
                        if from_date <= atten_time <= to_date:
                            # Convert the time to UTC for storage
                            utc_dt = atten_time.astimezone(pytz.utc)
                            utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                            atten_time = datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")
                            atten_time = fields.Datetime.to_string(atten_time)

                            # if user:
                            #     for uid in user:
                            #         if uid.user_id == each.user_id:

                            get_user_id = self.env['payroll.employees'].search([('nik', '=', each.user_id), ('department_id', '=', self.device_department_id.id)]) #, ('category_id.without_attendance_logs','=',False)
                            if get_user_id:
                                # duplicate_atten_ids = zk_attendance.search([('device_id', '=', each.user_id), ('punching_time', '=', atten_time)])
                                duplicate_atten_ids = self.env['payroll.attendance.device'].search([('nik', '=', each.user_id), ('punching_time', '=', atten_time), ('department', '=', self.device_department_id.id)])
                                if duplicate_atten_ids:
                                    continue
                                else:
                                    payroll_attendance_device.create({
                                        'employee_id': get_user_id.id,
                                        'punch_type': str(each.punch),
                                        'punching_time': atten_time,
                                        'device_id': each.user_id,
                                        #'attendance_type': str(each.status),
                                        'address_id': info.address_id.id,
                                        'department': info.device_department_id.name,
                                        'is_processed': False
                                    })
                            else:
                                new_employee_setup = self.env['payroll.scheduler.setup'].search([], limit=1)
                                employee = self.env['payroll.employees'].create({
                                    'name': each.user_id,
                                    'nik': each.user_id,
                                    'department_id': info.device_department_id.id,
                                    'company_id': new_employee_setup.default_company_employee.id,
                                    'active_date': fields.Date.today(),
                                    'working_status': '1',
                                    'contract_id': new_employee_setup.default_contract_employee.id,
                                    'current_website': new_employee_setup.default_website_employee.id,
                                    'category_id': new_employee_setup.default_category_employee.id,
                                    'current_position': new_employee_setup.default_position_employee.id,
                                })
                                payroll_attendance_device.create({
                                    'employee_id': employee.id,
                                    'punch_type': str(each.punch),
                                    'punching_time': atten_time,
                                    'device_id': each.user_id,
                                    #'attendance_type': str(each.status),
                                    'address_id': info.address_id.id,
                                    'department': info.device_department_id.name,
                                    'is_processed': False
                                })
                    # Convert `datetime.now(gmt_plus_7_tz)` to naive datetime before assigning
                    info.last_date_run = fields.Datetime.now()
                    conn.disconnect()
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))
            
    def run_scheduled_attendance_download(self):
        machines = self.search([('department', '!=', False)])
        for machine in machines:
            try:
                machine.download_attendance_2()
                _logger.info(f"Successfully processed machine {machine.name}")
            except Exception as e:
                # Log any errors during execution
                _logger.error(f"Error processing machine {machine.name}: {e}")