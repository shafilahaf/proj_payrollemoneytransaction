from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError

# class BackofficeXlsx(models.AbstractModel):
#     _name = "report.report_xlsx.backoffice_xlsx"
#     _inherit = "report.report_xlsx.abstract"
#     _description = "Backoffice XLSX Report"

#     def generate_xlsx_report(self, workbook, data, partners):
#         sheet = workbook.add_worksheet("Report")
#         for i, obj in enumerate(partners):
#             bold = workbook.add_format({"bold": True})
#             sheet.write(i, 0, obj.name, bold)