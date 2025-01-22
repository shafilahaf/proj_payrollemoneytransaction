from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PayrollPositions(models.Model):
    _name = 'payroll.positions'
    _description = 'Positions'
    _rec = 'name'
    _sql_constraints = [
        ('name_unique',
         'UNIQUE(name)',
         'Position name must be unique!'),
    ]

    name = fields.Char(string='Name', required=True)
    level = fields.Integer(string='Level', required=True)
    late_tolerance = fields.Integer(string='Late Tolerance')
    late_tolerance_2 = fields.Integer(string='Late Tolerance 2')
    late_tolerance_3 = fields.Integer(string='Late Tolerance 3')
    late_tolerance_4 = fields.Integer(string='Late Tolerance 4')
    active = fields.Boolean(string='Active', default=True)

    position_approver_ids = fields.One2many('payroll.positions.approver', 'position_id', string='Approvers')

class PayrollPositionsApprover(models.Model):
    _name = 'payroll.positions.approver'
    _description = 'Positions Approver'

    sequence = fields.Integer(string='Sequence', required=True)
    position_id = fields.Many2one('payroll.positions', string='Position', required=True)
    approver_position_id = fields.Many2one('payroll.positions', string='Approver Position', required=True, domain="[('id', '!=', position_id)]")