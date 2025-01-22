from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)
class PayrollAttDevicetoLog(models.TransientModel):
    _name = 'payroll.convert.att.device.to.log'
    _description = 'Payroll Convert Attendance Device to Log'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def convert_att_device_to_log_all_dept(self):
        machines = self.env['zk.machine'].search([])  # Search for all machines
        for machine in machines:
            try:
                machine.convert_att_log(self.start_date, self.end_date)
                _logger.info(f"Completed scheduled convert_att_log for machine: {machine.name}")
            except Exception as e:
                raise ValidationError(f"Error while converting attendance log for machine {machine.name}: {e}")