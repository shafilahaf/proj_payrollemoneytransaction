from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

# Variabel Set Selections Fields --START
setSelectionSource = [
    ("1", "Absence"),
    ("2", "Permission"),
    ("3", "Sick"),
    ("4", "Late 1"),
    ("5", "Late 2"),
    ("6", "Device Error"),
    ("7", "Forget Checkout"),
    ("8", "Leave"),
    ("9", "Late 3"),
    ("10", "Late 4"),
]
# Variabel Set Selections Fields --END


class PayrollAttendanceLogPoint(models.Model):
    _name = "payroll.attendance.log.point"
    _description = "Attendance Log Point"
    _rec_name = 'source'

    source = fields.Selection(setSelectionSource, string="Source", required=True)
    point = fields.Integer(string="Point", required=True)
