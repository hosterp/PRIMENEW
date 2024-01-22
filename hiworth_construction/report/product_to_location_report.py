from openerp import fields, models, api
import datetime, calendar
from openerp.osv import osv
from decimal import Decimal

class stock_locaton(models.Model):
    _inherit = 'stock.location'
    
    temp_product_qty = fields.Float('Temp Product Qty', default=0.0)
    temp_inventry_value = fields.Float('Temp Inventory Value', default=0.0)
    temp_avg_unit_price = fields.Float('Temp Avg Price', default=0.0)


class report_product(models.TransientModel):
    _name = 'report.product'
    
    @api.onchange('product_id')
    def onchange_category(self):
        if self.report_id.category_id.id != False:
            return {
                'domain': {
                        'product_id':[('categ_id','=', self.report_id.category_id.id)]
                    }
                }
    
    product_id = fields.Many2one('product.product', 'Product')
    report_id = fields.Many2one('product.to.location.report')
    
    
class report_locaton(models.TransientModel):
    _name = 'report.location'
    
    location_id = fields.Many2one('stock.location', 'Location')
    report_id = fields.Many2one('product.to.location.report')
    


class product_to_location_report(models.TransientModel):
    _name='product.to.location.report'
    

    from_date = fields.Date(default=lambda self: self.default_time_range('from'))
    to_date = fields.Date(default=lambda self: self.default_time_range('to'))
    select_product = fields.Boolean('Select Product')
    category_id = fields.Many2one('product.category', 'Category')
    product_ids = fields.One2many('report.product', 'report_id', 'Products') 
    select_location = fields.Boolean('Select Location')
    location_ids = fields.One2many('report.location', 'report_id', 'Location')
    
    


    # Calculate default time ranges
    @api.model
    def default_time_range(self, type):
        year = datetime.date.today().year
        month = datetime.date.today().month
        last_day = calendar.monthrange(datetime.date.today().year,datetime.date.today().month)[1]
        first_day = 1
        if type=='from':
            return datetime.date(year, month, first_day)
        elif type=='to':
            return datetime.date(year, month, last_day)

    @api.multi
    def print_product_to_location_report(self):
        self.ensure_one()
    
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_product_to_location_template',
            'datas': datas,
#             'report_type': 'qweb-pdf',
            
        }
        
    @api.multi
    def view_product_to_location_report(self):
        self.ensure_one()
        
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_product_to_location_template',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date,'source': self.source.name,'destination': self.destination.name}
            'report_type': 'qweb-html',
        }
        
        
    @api.multi
    def get_products(self):
        self.ensure_one() 
        
        
        if self.category_id.id != False and self.select_product == False:
            products = self.env['product.product'].search([('type','=','product'),('categ_id','=',self.category_id.id)])
            recordset = products.sorted(key=lambda r: r.name)
#             print 'products==================', recordset
            return recordset
            
        if self.select_product == True:
            product_ids = []
            product_ids = [product.product_id.id for product in self.product_ids]
            if product_ids == []:
                raise osv.except_osv(('Error'), ('Please select atleast one product or uncheck the box.'))    
        
            products = self.env['product.product'].search([('id','in',product_ids)])
            recordset = products.sorted(key=lambda r: r.name)
#             print 'products==================', recordset
            return recordset
        if self.select_product == False:
            products = self.env['product.product'].search([('type','=','product')])
            recordset = products.sorted(key=lambda r: r.categ_id)
            return recordset
            
    @api.multi
    def get_locations(self,product_id):
        self.ensure_one()
        
#         print 'product=================================', product_id
        if self.select_location == True:
            location_ids = []
            location_ids = [location.location_id.id for location in self.location_ids]
            if location_ids == []:
                raise osv.except_osv(('Error'), ('Please select atleast one Location or uncheck the box.'))    
        
            locations = self.env['stock.location'].search([('id','in',location_ids),('usage','=','internal')])
#             print 'locations===============', locations,location_ids
            for location in locations:
                moves = self.env['stock.move'].search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('product_id','=', product_id.id),('location_dest_id','=', location.id)])
#                 print 'locarions========================', location
                location.temp_product_qty = 0.0
                location.temp_inventry_value = 0.0
                location.temp_avg_unit_price = 0.0
                for move in moves:
                    location.temp_product_qty += move.product_uom_qty
                    location.temp_inventry_value += move.inventory_value
                if location.temp_product_qty  != 0.0:
                    temp_avg_price_decimal = Decimal(location.temp_inventry_value/location.temp_product_qty)
                    location.temp_avg_unit_price = round(temp_avg_price_decimal,2)
            recordset = locations.sorted(key=lambda r: r.name)
            return recordset
        
        if self.select_location == False:
#             print 'uid================', self.env['res.company']._company_default_get('product.to.location.report'),self.env.user,sdfsdf
            warehouse = self.pool.get('stock.warehouse').search(self.env.cr, self.env.uid, [('company_id', '=', self.env.user.company_id.id)], limit=1)
            loc_id = self.env['stock.warehouse'].search([('id','=',warehouse[0])]).lot_stock_id
            locations = self.env['stock.location'].search([('id','!=',loc_id.id),('usage','=','internal')])
            
            for location in locations:
                moves = self.env['stock.move'].search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('product_id','=', product_id.id),('location_dest_id','=', location.id)])
#                 print 'locarions========================', location
                location.temp_product_qty = 0.0
                location.temp_inventry_value = 0.0
                location.temp_avg_unit_price = 0.0
                for move in moves:
                    location.temp_product_qty += move.product_uom_qty
                    location.temp_inventry_value += move.inventory_value
#                     print 'value===================', location.temp_inventry_value
                if location.temp_product_qty  != 0.0:
                    temp_avg_price_decimal = Decimal(location.temp_inventry_value/location.temp_product_qty)
                    location.temp_avg_unit_price = round(temp_avg_price_decimal,2)
            
            recordset = locations.sorted(key=lambda r: r.name)
#             print 'locations==================', recordset
            return recordset 
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
