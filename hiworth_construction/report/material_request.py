from openerp import models, fields, api

class MaterialRequest(models.Model):
    _inherit='stock.picking'

    @api.model
    def get_move_line(self, picking_id):
        return self.env['stock.picking'].browse(picking_id).move_lines
