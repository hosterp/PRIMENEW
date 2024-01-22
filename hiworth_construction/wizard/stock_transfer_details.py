from openerp import models, fields, api
from openerp.exceptions import Warning
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import datetime


class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'
    
    
    add_carriage = fields.Boolean('Add Carriage Charges')
    
    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(stock_transfer_details, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.picking'), 'Bad context propagation'
        picking_id, = picking_ids
        picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        items = []
        packs = []
        if not picking.pack_operation_ids:
            picking.do_prepare_partial()
        for op in picking.pack_operation_ids:
            item = {
                'packop_id': op.id,
                'product_id': op.product_id.id,
                'product_uom_id': op.product_uom_id.id,
                'quantity': op.product_qty,
                'package_id': op.package_id.id,
                'lot_id': op.lot_id.id,
                'sourceloc_id': op.location_id.id,
                'destinationloc_id': op.location_dest_id.id,
                'result_package_id': op.result_package_id.id,
                'date': op.date, 
                'owner_id': op.owner_id.id,
            }
            if op.product_id:
                items.append(item)
            elif op.package_id:
                packs.append(item)
        res.update(item_ids=items)
        res.update(packop_ids=packs)
        return res
    
    @api.one
    def do_detailed_transfer(self):
        if self.picking_id.state not in ['assigned', 'partially_available']:
            raise Warning(_('You cannot transfer a picking in state \'%s\'.') % self.picking_id.state)

        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                }
                if prod.packop_id:
                    prod.packop_id.with_context(no_recompute=True).write(pack_datas)
                    processed_ids.append(prod.packop_id.id)
                else:
                    pack_datas['picking_id'] = self.picking_id.id
                    packop_id = self.env['stock.pack.operation'].create(pack_datas)
                    processed_ids.append(packop_id.id)
        # Delete the others
        packops = self.env['stock.pack.operation'].search(['&', ('picking_id', '=', self.picking_id.id), '!', ('id', 'in', processed_ids)])
        packops.unlink()

        # Execute the transfer of the picking
        self.picking_id.do_transfer()
        
     #   pro_obj = self.env['produt.template']
        cost_obj = self.env['product.cost.table']
        
        for line in self:
            for lines in line.item_ids:
                if lines.new_price_unit != lines.price_unit:
                    cost_table = []
                    coast_table = [table.id for table in lines.product_id.product_tmpl_id.cost_table_id]
                    if len(coast_table) == 0:
                        vals = {
                            'product_id': lines.product_id.product_tmpl_id.id,
#                             'date': line.picking_id.date,
                            'standard_price': lines.product_id.product_tmpl_id.standard_price,
                            'purchase_id': 'Initial cost'}
                        cost_id1 = cost_obj.create(vals)
                    
                    vals = {
                            'product_id': lines.product_id.product_tmpl_id.id,
                            'date': line.picking_id.date,
                            'standard_price': lines.new_price_unit,
                            'purchase_id': line.picking_id.origin}
                    
                    cost_id = cost_obj.create(vals)
                    
                    lines.product_id.product_tmpl_id.old_price = lines.product_id.product_tmpl_id.standard_price 
                    lines.product_id.product_tmpl_id.standard_price = lines.new_price_unit
                    print 'ooooooooooooooooooooooooooo',lines.product_id.product_tmpl_id.old_price,lines.product_id.product_tmpl_id.standard_price
                

        return True
    
    
class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'
    
    @api.multi
    @api.depends('carriage')
    def _compute_new_cost(self):
          
        for line in self:
   #         print 'testfffffffffff22222222222222222'
            line.new_price_unit = line.current_rate +(line.carriage/line.quantity)
            
    @api.multi
    @api.depends('product_id')
    def _compute_purchasing_cost(self):
          
        for line in self:
            for move in line.transfer_id.picking_id.move_lines:
                if line.product_id == move.product_id:
                    line.current_rate = move.price_unit
            
    
    
    price_unit = fields.Float(related='product_id.standard_price', store=True, string='Unit Price')
    current_rate = fields.Float(compute='_compute_purchasing_cost', store=True, string='Current Rate')
    carriage = fields.Float('Carriage')
    new_price_unit = fields.Float(compute='_compute_new_cost', store=True, string="New Cost")
