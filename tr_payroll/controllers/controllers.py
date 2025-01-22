# -*- coding: utf-8 -*-
# from odoo import http


# class TrPayroll(http.Controller):
#     @http.route('/tr_payroll/tr_payroll', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tr_payroll/tr_payroll/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tr_payroll.listing', {
#             'root': '/tr_payroll/tr_payroll',
#             'objects': http.request.env['tr_payroll.tr_payroll'].search([]),
#         })

#     @http.route('/tr_payroll/tr_payroll/objects/<model("tr_payroll.tr_payroll"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tr_payroll.object', {
#             'object': obj
#         })
