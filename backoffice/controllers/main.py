from lxml import etree as ElementTree

from odoo.http import Controller, route, request

class Board(Controller):
    @route('/web/view/edit_custom', type='json', auth="user")
    def edit_custom(self, arch):
        return {'result': True}