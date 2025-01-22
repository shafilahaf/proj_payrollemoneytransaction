# -*- coding: utf-8 -*-
{
    'name': "Payroll Management",
    'author': "Trusta",
    'category': 'Payroll/PayrollManagement',
    'version': '0.1',
    'depends': ['base', 'mail', 'hr_zk_attendance'],
    'data': [
        'security/payroll.xml',
        'security/ir.model.access.csv',
        # 'views/assets.xml',
        'views/payroll_banks.xml',
        'views/payroll_benefits.xml',
        'views/payroll_device_department.xml',
        'views/payroll_companies.xml',
        'views/payroll_contracts.xml',
        'views/payroll_countries.xml',
        'views/payroll_currencies.xml',
        'views/payroll_deductions.xml',
        'views/payroll_employee_status.xml',
        'views/payroll_positions.xml',
        'views/payroll_salary_component.xml',
        'views/payroll_shifts.xml',
        'views/payroll_employee_categories.xml',
        'views/payroll_employees.xml',
        'views/payroll_mistake_entries.xml',
        'views/payroll_time_off_request.xml',
        'views/payroll_employee_move.xml',
        'views/payroll_salary_adjustment.xml',
        'views/payroll_emp_appraisals.xml',
        'views/payroll_absence_register.xml',
        'views/payroll_approval_entreis.xml',
        'views/payroll_attendance_device.xml',
        'views/payroll_ph_health.xml',
        'views/mail_channel_inherit.xml',
        'wizard/payroll_mistake_entries_wizard.xml',
        'wizard/payroll_shift_assign.xml',
        'views/payroll_attendance_log.xml',
        'views/payroll_payroll_summaries.xml',
        'views/payroll_key_performance_index.xml',
        'views/report/report.xml',
        'views/report/report_payroll_summaries_pdf.xml',
        'views/report/report_kpi_template_pdf.xml',
        'wizard/payroll_calculate_benefit_leaves_wizard.xml',
        'wizard/payroll_recalculate_attendance_log_late_wizard.xml',
        'wizard/payroll_moving_employee_wizard.xml',
        'wizard/payroll_import_excel_employee_wizard.xml',
        'wizard/calculate_salary.xml',
        'wizard/payroll_kpi_report_excel_wizard.xml',
        'wizard/payroll_summaries_report_excel.xml',
        'wizard/payroll_summaries_ph_report_excel.xml',
        'wizard/payroll_attendance_log_report_excel_wizard.xml',
        'wizard/payroll_sync_mistake_detail.xml',
        'wizard/payroll_salary_adjustment_bulk.xml',
        'wizard/config.xml',
        'wizard/convert_attendance_device_to_log.xml',
        'wizard/change_password_user.xml',
        'wizard/payroll_my_profile_wizard.xml',
        'views/zk_machine_inherit.xml',
        'views/zk_report_daily_att.xml',
        'views/payroll_shift_assign.xml',
        'views/payroll_attendance_log_point.xml',
        'views/payroll_holiday.xml',
        'views/payroll_employee_detail.xml',
        'views/payroll_mistake_detail.xml',
        'views/res_users_inherit.xml',
        'views/res_groups_inherit.xml',
        'views/payroll_restrict.xml',
        # 'views/user_menu_inherit.xml',
        'views/menu/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'tr_payroll/static/src/js/*.js'
        ],
        'web.assets_qweb': [
            'tr_payroll/static/src/xml/*.xml'
        ],
    },
}
