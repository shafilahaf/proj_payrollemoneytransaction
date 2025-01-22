from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from datetime import date, timedelta
import logging

_logger = logging.getLogger(__name__)


class PayrollEmployees(models.Model):
    _name = "payroll.employees"
    _description = "Payroll Employees"
    _rec_name = "name"
    _sql_constraints = [
        ("nik_unique", "CHECK(1==1)", "NIK must be unique!"),
        ("username_unique", "CHECK(1==1)", "Username must be unique!"),
    ]

    # General Information
    name = fields.Char(string="Name", required=True)
    nik = fields.Char(string="NIK", required=True)
    username = fields.Char(string="Username")
    address = fields.Text(string="Address")
    address_2 = fields.Text(string="Address 2")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")
    emergency_contact = fields.Char(string="Emergency Contact")
    emergency_phone = fields.Char(string="Emergency Phone")
    gender = fields.Selection([("1", "Male"), ("2", "Female")], string="Gender")
    active = fields.Boolean(string="Active", default=True)

    manager_id = fields.Many2one(
        "payroll.employees",
        string="Manager",
        domain="[('current_position', 'ilike', 'manager')]",
    )
    active_leave_date = fields.Date(string="Active Leave Date")
    active_date = fields.Date(string="Active Date", required=True)
    inactive_date = fields.Date(string="Inactive Date")
    working_status = fields.Selection(
        [
            ("1", "Active"),
            ("2", "Inactive"),
            ("3", "Terminated"),
        ],
        string="Working Status",
        required=True,
    )

    contract_id = fields.Many2one("payroll.contracts", string="Contract", required=True)
    contract_start_date = fields.Date(string="Contract Start Date")
    contract_end_date = fields.Date(string="Contract End Date")
    employee_status_id = fields.Many2one(
        "payroll.employee.status", string="Employee Status"
    )
    company_id = fields.Many2one("payroll.companies", string="Company", required=True)
    current_website = fields.Many2one(
        "payroll.websites", string="Current Website", required=True
    )
    department_id = fields.Many2one(
        "payroll.device.department", string="Department", required=True
    )
    category_id = fields.Many2one(
        "payroll.employee.categories", string="Category", required=True
    )
    current_position = fields.Many2one(
        "payroll.positions", string="Current Position", required=True
    )
    last_leave_date = fields.Date(string="Last Leave Date")
    notes_last_leave_date = fields.Char('Note', size=100)
    next_leave_date = fields.Date(
        string="Next Leave Date (Estimate Date)", 
        compute="_compute_next_leave_date",
        store=True)
    
    remaining_sick_leave = fields.Integer(string="Remaining Sick Leave", compute="_compute_remaining_sick_leave")

    # Administration
    date_of_birth = fields.Date(string="Date of Birth")
    country_id = fields.Many2one("payroll.countries", string="Country of Birth")
    city_id = fields.Many2one(
        "payroll.cities",
        string="City of Birth",
        domain="[('countries_id', '=', country_id)]",
    )
    visa_number = fields.Char(string="Visa Number")
    visa_expire_date = fields.Date(string="Visa Expire Date")
    passport_number = fields.Char(string="Passport Number")
    passport_expire_date = fields.Date(string="Passport Expire Date")
    case_of_inactivity = fields.Char(string="Case of Inactivity")
    bank_id = fields.Many2one("payroll.banks", string="Bank")
    bank_account_number = fields.Char(string="Bank Account Number")
    user_id = fields.Many2one("res.users", string="User", store=True, readonly=True)
    bank_account_holder_name = fields.Char(string="Bank Accout Holder Name")

    # Salary
    emp_salary_ids = fields.One2many(
        "payroll.employee.salary", "employee_id", string="Salary"
    )

    # Shift
    emp_shift_ids = fields.One2many(
        "payroll.employee.shift", "employee_id", string="Shift"
    )

    # Deduction
    emp_deduction_ids = fields.One2many(
        "payroll.employee.deduction", "employee_id", string="Deduction"
    )

    picture = fields.Binary(string="Picture")
    is_moving = fields.Boolean(string="Is Moving")

    can_edit_nik_dept = fields.Boolean(
        string="Can Edit NIK and Department",
        compute="_compute_can_edit_nik_dept",
        store=False,
    )

    @api.constrains("user_id", "username")
    def _check_username(self):
        for record in self:
            if record.user_id and not record.username:
                raise ValidationError("Username must be set if user_id is set.")

    # Get remaining_sick_leave
    def _compute_remaining_sick_leave(self):
        for record in self:
            employee_medical_benefit = self.env['payroll.employee.details'].search([
                ('employee_id', '=', record.id),
                ('type', '=', '3'),
                ('isActive', '=', True)
            ])

            if employee_medical_benefit:
                time_off_req = self.env['payroll.time.off.request'].search([
                    ('employee_id', '=', record.id),
                    ('request_type', '=', '2'),
                    ('status', '=', '5'),
                    ('start_date', '>=', employee_medical_benefit[0].active_date),
                    ('end_date', '<=', employee_medical_benefit[0].expired_date)
                ])
                if time_off_req:
                    record.remaining_sick_leave = sum([med.quantity for med in employee_medical_benefit]) - sum([req.duration for req in time_off_req])
                else:
                    record.remaining_sick_leave = sum([med.quantity for med in employee_medical_benefit])
            else:
                record.remaining_sick_leave = 0



    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Override the search method to restrict employees based on user groups and department/category logic."""
        user = self.env.user
        user_groups = user.groups_id

        allowed_departments = []
        allowed_categories = []

        for group in user_groups:
            if group.is_active:
                allowed_departments += group.department_ids.ids
                allowed_categories += group.categories_ids.ids

        # domain = [] 
        
        # if allowed_departments and allowed_categories:
        #     for dept in allowed_departments:
        #         for cat in allowed_categories:
        #             domain += ['|',('department_id', '=', dept), ('category_id', '=', cat)]
        # elif allowed_departments:
        #     for dept in allowed_departments:
        #         domain += [('department_id', '=', dept)]
        # elif allowed_categories:
        #     for cat in allowed_categories:
        #         domain += [('category_id', '=', cat)]

        domain = []
        if allowed_departments and allowed_categories:
            domain = ['|', ('department_id', 'in', allowed_departments), ('category_id', 'in', allowed_categories)]
        elif allowed_departments:
            domain = [('department_id', 'in', allowed_departments)]
        elif allowed_categories:
            domain = [('category_id', 'in', allowed_categories)]

        if domain:
            args += domain

        return super(PayrollEmployees, self).search(args, offset, limit, order, count)


    @api.depends('user_id')
    def _compute_can_edit_nik_dept(self):
        for record in self:
            user = self.env.user
            record.can_edit_nik_dept = any(
                group.permitted_edit_nik_dept for group in user.groups_id
            )

    @api.onchange("category_id")
    def _onchange_category_id(self):
        """
        This method is called when the category_id field is changed."""
        if self.category_id:
            # Clear existing salary lines
            self.emp_salary_ids = [(5, 0, 0)]

            salary_comp = []
            for rec in self.category_id.salary_components_ids:
                salary_comp.append(
                    (
                        0,
                        0,
                        {
                            "salary_component_id": rec.salary_component_id.id,
                            "currency_id": rec.currency_id.id,
                            "amount": rec.amount,
                            "recurring": rec.recurring,
                            "minimum_working_duration": rec.minimum_working_duration,
                            "meal_type": rec.meal_type,
                            "pro_rate": rec.pro_rate,
                            "is_basic_salary": rec.is_basic_salary,
                            "condition": rec.condition,
                        },
                    )
                )

            self.emp_salary_ids = salary_comp

    @api.onchange("contract_start_date")
    def _onchange_contract_start_date(self):
        """
        This method is called when the contract_start_date field is changed."""
        if self.contract_start_date:
            self.contract_end_date = self.contract_start_date + relativedelta(
                months=self.contract_id.period
            )

    @api.model
    def create(self, vals):
        """
        This method is called when creating a new record."""
        res = super(PayrollEmployees, self).create(vals)

        # Format username: lowercased name + nik + department
        username = (
            f"{res.name.lower().replace(' ', '')}{res.nik}-{res.department_id.name}"
        )

        # Search group where  Category_id : PayrollManagement and Name = Staff
        mod_category = self.env['ir.module.category'].search([('name', '=', 'PayrollManagement')], limit=1)
        payroll_group = self.env['res.groups'].search([('category_id', '=', mod_category.id), ('name','ilike','Staff')], limit=1)


        # Create the user
        group = self.env['res.groups'].search([('full_name', '=', 'Staff')], limit=1)
        user = self.env["res.users"].create(
            {
                # "name": res.name,
                "name": f"{res.name.lower().replace(' ', '')}{res.nik}-{res.department_id.name}", # Leo minta ganti ditanggal 1/3/2025
                "login": f"{res.name.lower().replace(' ', '')}{res.nik}-{res.department_id.name}",
                "password": "user",
                "groups_id": [(6, 0, [self.env.ref('base.group_user').id, payroll_group.id])],
            }
        )

        res.username = user.login

        partner = self.env["res.partner"].search([("name", "=", res.name)], limit=1)
        if partner:
            partner.write({"email": f"{username}@example.com"})

        res.user_id = user.id

        if res.department_id:
            user.write({"department_ids": [(6, 0, [res.department_id.id])]})

        return res

    def write(self, vals):
        """
        Override the write method to update the associated user details
        when the employee's details are updated, avoiding recursion.
        """
        # Check if we are already in the middle of a sync operation
        if self.env.context.get("prevent_recursion"):
            return super(PayrollEmployees, self).write(vals)

        result = super(PayrollEmployees, self).write(vals)

        for employee in self:
            if employee.user_id:
                user_updates = {}

                # Update username
                if "username" in vals:
                    user_updates["login"] = vals.get("username")

                # Updating ResUsers fields when PayrollEmployees is updated
                if "name" in vals:
                    user_updates["name"] = vals.get("name")
                # if "department_id" in vals:
                #     user_updates["department_ids"] = [
                #         (6, 0, [vals.get("department_id")])
                #     ]
                if "address" in vals:
                    user_updates["payroll_address"] = vals.get("address")
                if "address_2" in vals:
                    user_updates["payroll_address_2"] = vals.get("address_2")
                if "phone" in vals:
                    user_updates["payroll_phone"] = vals.get("phone")
                if "email" in vals:
                    user_updates["payroll_email"] = vals.get("email")
                if "emergency_contact" in vals:
                    user_updates["payroll_emergency_contact"] = vals.get(
                        "emergency_contact"
                    )
                if "emergency_phone" in vals:
                    user_updates["payroll_emergency_phone"] = vals.get(
                        "emergency_phone"
                    )
                if "gender" in vals:
                    user_updates["payroll_gender"] = vals.get("gender")
                if "date_of_birth" in vals:
                    user_updates["payroll_date_of_birth"] = vals.get("date_of_birth")
                if "country_id" in vals:
                    user_updates["payroll_country_id"] = vals.get("country_id")
                if "city_id" in vals:
                    user_updates["payroll_city_id"] = vals.get("city_id")
                if "visa_number" in vals:
                    user_updates["payroll_visa_number"] = vals.get("visa_number")
                if "visa_expire_date" in vals:
                    user_updates["payroll_visa_expire_date"] = vals.get(
                        "visa_expire_date"
                    )
                if "passport_number" in vals:
                    user_updates["payroll_passport_number"] = vals.get(
                        "passport_number"
                    )
                if "passport_expire_date" in vals:
                    user_updates["payroll_passport_expire_date"] = vals.get(
                        "passport_expire_date"
                    )
                if "bank_id" in vals:
                    user_updates["payroll_bank_id"] = vals.get("bank_id")
                if "bank_account_number" in vals:
                    user_updates["payroll_bank_account_number"] = vals.get(
                        "bank_account_number"
                    )

                if vals.get("is_moving", False) == False:
                    if "name" in vals or "nik" in vals or "department_id" in vals:
                        username = f"{vals.get('name', employee.name).replace(' ', '')}{vals.get('nik', employee.nik)}-{employee.department_id.name}"
                        user_updates["name"] = username
                        user_updates["login"] = username

                    # Avoid recursion by passing a flag in the context
                    if user_updates:
                        employee.user_id.with_context(prevent_recursion=True).write(
                            user_updates
                        )

                    # Update partner email (if needed)
                    username = f"{employee.name.lower().replace(' ', '')}{employee.nik}{employee.department_id.name}"
                    partner = self.env["res.partner"].search(
                        [("name", "=", employee.name)], limit=1
                    )
                    if partner:
                        partner.write({"email": f"{username}@example.com"})

                if "category_id" in vals and employee.category_id:
                    employee._onchange_category_id()

        return result

    def unlink(self):
        """
        Override unlink method to delete associated res.users records."""
        for employee in self:
            if employee.user_id:
                employee.user_id.unlink()  # Delete the associated res.users record
        return super(PayrollEmployees, self).unlink()
    
    @api.depends('last_leave_date')
    def _compute_next_leave_date(self):
        for record in self:
            if record.last_leave_date:
                record.next_leave_date = record.last_leave_date + timedelta(days=182)
            else:
                record.next_leave_date = False
    
    def update_missing_usernames(self):
        """
        Update missing usernames from the login field in res.users.
        """
        employees = self.search([('username', '=', False), ('user_id', '!=', False)])
        for employee in employees:
            if employee.user_id.login:
                employee.username = employee.user_id.login
                employee.user_id.login = employee.username
    
class PayrollEmployeeSalary(models.Model):
    _name = "payroll.employee.salary"
    _description = "Payroll Employee Salary"

    employee_id = fields.Many2one(
        "payroll.employees", string="Employee", ondelete="cascade"
    )
    salary_component_id = fields.Many2one(
        "payroll.salary.components", string="Salary Component", required=True
    )
    currency_id = fields.Many2one(
        "payroll.currencies", string="Currency", required=True
    )
    amount = fields.Float(string="Amount", required=True)
    recurring = fields.Integer(string="Recurring")
    minimum_working_duration = fields.Integer(string="Minimum Working Duration")
    meal_type = fields.Selection(
        [("1", "Give After"), ("2", "Upfront"), ("3", "Day Rate")], string="Meal Type"
    )
    pro_rate = fields.Boolean(string="Pro Rate")
    is_basic_salary = fields.Boolean(string="Is Basic Salary")
    condition = fields.Selection(
        [("1", "No Mistake"), ("2", "Not Taken Leaves")], string="Condition"
    )
    last_increment_salary_date = fields.Date(string="Last Increment Salary Date")
    last_increment_salary_amount = fields.Float(string="Last Increment Salary Amount")

    @api.onchange("salary_component_id")
    def _onchange_salary_component_id(self):
        self.is_basic_salary = self.salary_component_id.is_basic_salary


class PayrollEmployeeShift(models.Model):
    _name = "payroll.employee.shift"
    _description = "Payroll Employee Shift"

    employee_id = fields.Many2one(
        "payroll.employees", string="Employee", required=True, ondelete="cascade"
    )
    shifts_id = fields.Many2one("payroll.shifts", string="Shift")
    start_date = fields.Date(
        string="Start Date", required=True, default=fields.Date.today()
    )
    end_date = fields.Date(string="End Date")
    companies_id = fields.Many2one("payroll.companies", string="Company")
    website_id = fields.Many2one(
        "payroll.websites",
        string="Website",
        domain="[('companies_id', '=', companies_id)]",
    )
    is_night_diff = fields.Boolean(string="Night Differential")
    shift_assign_id = fields.Integer(string="Shift Assign Id")

    @api.onchange("employee_id")
    def _onchange_employee_id(self):
        """
        This method is called when the employee_id field is changed."""
        self.companies_id = self.employee_id.company_id.id


class PayrollEmployeeDeduction(models.Model):
    _name = "payroll.employee.deduction"
    _description = "Payroll Employee Deduction"

    employee_id = fields.Many2one(
        "payroll.employees", string="Employee", required=True, ondelete="cascade"
    )
    deduction_id = fields.Many2one(
        "payroll.deductions", string="Deduction", required=True
    )
    currency_id = fields.Many2one(
        "payroll.currencies", string="Currency", required=True
    )
    amount = fields.Float(string="Amount", required=True)
