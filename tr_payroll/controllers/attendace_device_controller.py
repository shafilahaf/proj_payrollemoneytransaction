from odoo import http
from odoo.http import request
from datetime import datetime
import logging
from odoo.addons.project_api.models.common import invalid_response, valid_response
import pytz
import functools

def validate_token(func):
    @functools.wraps(func)
    def wrap(self, *args, **kwargs):
        access_token = request.httprequest.headers.get("access_token")
        if not access_token:
            return invalid_response("access_token_not_found", "missing access token in request header", 401)
        access_token_data = request.env["api.access_token"].sudo().search([("token", "=", access_token)],
                                                                          order="id DESC", limit=1)

        if access_token_data.find_or_create_token(user_id=access_token_data.user_id.id) != access_token:
            return invalid_response("access_token", "token seems to have expired or invalid", 401)

        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        return func(self, *args, **kwargs)

    return wrap

_logger = logging.getLogger(__name__)

class AttendaceDeviceController(http.Controller):
    @validate_token
    @http.route('/api/payroll_att_device', auth='none', methods=['POST'], csrf=False, type='json')
    def create_attendance_device(self, **kw):
        """
        Create a new Unit of Measure
        """
        data = request.jsonrequest
        nik = data.get('Nik')
        punching_time = data.get('PunchTime')
        punch_type = data.get('PunchState')
        department = data.get('Department')

        try:
            # Punching Time GMT-7 TZ
            punching_time = datetime.strptime(punching_time, '%Y-%m-%dT%H:%M:%S')
            punching_time_utc = pytz.utc.localize(punching_time)
            punching_time_gmt_minus7 = punching_time_utc.astimezone(pytz.timezone('Etc/GMT+7'))  # GMT-7
            # Punching Time GMT-7 TZ

            # punching_time2 = punching_time.replace("T"," ")
            punching_time2 = punching_time_gmt_minus7.strftime('%Y-%m-%d %H:%M:%S')
            att_device = request.env['payroll.attendance.device'].sudo()
            existing_record = att_device.search([
                ('nik', '=', nik),
                ('punching_time', '=', punching_time2),
                ('punch_type', '=', punch_type),
                ('department', '=', department)
            ], limit=1)

            if existing_record:
                return {
                    'message': 'Attendance Device record already exists',
                    'response': 200
                }
            
            att_device.create({
                'nik': nik,
                'punching_time': punching_time2,
                'punch_type' : punch_type,
                'department' : department
            })
            return {
                'message': 'Attendance Device created successfully',
                'response': 200
            }

        except Exception as e:
            _logger.error("Error creating Attendance Device: %s", e)
            return {
                'error': str(e),
                'response': 500
            }

    @validate_token
    @http.route('/api/payroll_att_employee', auth='none', methods=['POST'], csrf=False, type='json')
    def create_attendance_employee(self, **kw):
        """
        Create a new Unit of Measure
        """
        data = request.jsonrequest
        nik = data.get('NIK')
        name = data.get('Name')
        department = data.get('Department')

        att_emp = request.env['payroll.employees'].sudo()
        dept = request.env['payroll.device.department'].sudo()

        dept = dept.search([
            ('name','=',department)
        ])
        if dept :
            att_emp = att_emp.search([('nik', '=', nik),('department_id','=',dept.id)])

            if att_emp :
                try:
                    att_emp.write({
                        'nik': nik,
                        'name': name
                    })
                    return {
                        'message': 'Attendace Employee updated successfully',
                        'response': 200
                    }
                except Exception as e:
                    _logger.error("Error update Attendace Employee: %s", e)
                    return {
                        'error': str(e),
                        'response': 500
                    }