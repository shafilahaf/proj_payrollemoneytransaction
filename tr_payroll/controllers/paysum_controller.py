from odoo import http
from odoo.http import request

class PayrollReportController(http.Controller):
    @http.route('/report/payroll_summary/<int:doc_id>', type='http', auth='user')
    def preview_payroll_summary(self, doc_id, **kwargs):
        record = request.env['payroll.payroll.summaries'].browse(doc_id)

        if not record.exists():
            return request.not_found()

        # Generate report
        report = request.env.ref('tr_payroll.report_payroll_sumarries_template')
        pdf_content, _ = report._render_qweb_pdf([doc_id])

        employee_name = record.employee_id.name or "Employee"
        month = record.month
        year = record.year
        title = f"{employee_name}/{month}/{year} - Payroll Summaries"

        response = request.make_response(pdf_content, [
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', f'inline; filename="{title}.pdf"')
        ])
        return response
