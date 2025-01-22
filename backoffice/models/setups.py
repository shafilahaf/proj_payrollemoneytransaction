from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class bl_setups(models.Model):
    _name = 'bo.setups'
    _description = 'Untuk kebutuhan setup di backoffice'
    _rec_name = 'name'

    name = fields.Char(string='Name', required=True)
    mistake_type = fields.Many2one('mistaketype.bo', string='Mistake Type')
    mistake_type_for_claim = fields.Many2one('mistaketype.bo', string='Mistake Type for Claim')
    category_for_claim = fields.Many2one('kategori.bo', string='Category for Claim')
    nominal_wd = fields.Float(string='Nominal WD', help="This field is used to set minimum nominal for withdrawal in backoffice (in IDR) needed to be approved")
    is_active = fields.Boolean(string='Active', default=False)

    @api.model
    def create(self, vals):
        if self.search_count([('is_active', '=', True)]) > 0:
            # raise Warning(_('Cannot create new setup because there is already active setup'))
            raise UserError(_('Cannot create new setup because there is already active setup'))
        return super(bl_setups, self).create(vals)
    
class backofficeDelete(models.TransientModel):
    _name = 'backoffice.delete'
    _description = 'Delete Backoffice Transaction Data'

    description = fields.Char(string='Description', default='Delete Backoffice Transaction Data (Backoffice and Bonus)', readonly=True)
    
    def delete_backoffice(self):
        self.env.cr.execute("DELETE FROM bo_header")
        self.env.cr.execute("DELETE FROM bo_bonus_header")

        return True
