from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
import time
from datetime import datetime
import datetime
from openerp.exceptions import except_orm, Warning, RedirectWarning
#from openerp.osv import fields
from openerp import tools
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from pychart.arrow import default
from cookielib import vals_sorted_by_key
# from pygments.lexer import _default_analyse
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
# from openerp.osv import osv
from openerp import SUPERUSER_ID

from lxml import etree



class mrp_bom_line(models.Model):
    _inherit = 'mrp.bom.line'

    @api.multi
    @api.depends('product_id','product_qty')
    def _compute_total_cost(self):

        for line in self:
            line.total_cost=line.product_id.standard_price*line.product_qty

    total_cost = fields.Float(compute='_compute_total_cost', store=True, string='Total Cost')


class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    @api.depends('bom_line_ids')
    def _compute_bom_cost(self):

        for line in self:
            for bom_lines in line.bom_line_ids:
                print 'tbom_lines======================',bom_lines, bom_lines.product_id
                line.bom_cost += bom_lines.product_id.standard_price*bom_lines.product_qty



    bom_cost = fields.Float(compute='_compute_bom_cost', store=True, string='BOM Cost')


    #   @api.multi
    def create(self, cr, uid, vals, context=None):

        print 'testf------------------------------',vals['product_tmpl_id'],vals['bom_line_ids']
        product_obj=self.pool.get('product.template').browse( cr, uid, [(vals['product_tmpl_id'])])
        bom_cost = 0.0
        for line in vals['bom_line_ids']:
            print 'aaaaaaaaaaaaaaaaaaaaaaaa', line[2]['product_id']
            product_obj2=self.pool.get('product.product').browse( cr, uid, [(line[2]['product_id'])])
            bom_cost += product_obj2.standard_price*line[2]['product_qty']
            print 'tttttttttttttttttttttttttttttttt', bom_cost

        #bom_cost = vals['bom_cost']
        product_obj.write({'standard_price':bom_cost,'list_price':bom_cost})
        print 'product_obj================================', product_obj.standard_price

        #print 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',asavals
        result = super(mrp_bom, self).create(cr, uid, vals, context=context)
        return result

class mrp_production(models.Model):
    _inherit = 'mrp.production'


    @api.multi
    @api.depends('bom_id')
    def _compute_estimated_cost(self):

        for line in self:
            for lines in line.bom_id:
                line.estimated_cost=lines.bom_cost


    estimated_cost = fields.Float(compute='_compute_estimated_cost', store=True, string='Estimated Cost')
    real_cost = fields.Float('Actual Host')

class task_category(models.Model):
    _name = 'task.category'


    @api.multi
    def name_get(self):
        def get_names(cat):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while cat:
                res.append(cat.name)
                cat = cat.parent_id
            return res

        return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]

    def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if not context:
            context = {}
        if name:
            # Be sure name_search is symetric to name_get
            categories = name.split(' / ')
            parents = list(categories)
            child = parents.pop()
            domain = [('name', operator, child)]
            if parents:
                names_ids = self.name_search(cr, uid, ' / '.join(parents), args=args, operator='ilike', context=context, limit=limit)
                category_ids = [name_id[0] for name_id in names_ids]
                if operator in expression.NEGATIVE_TERM_OPERATORS:
                    category_ids = self.search(cr, uid, [('id', 'not in', category_ids)])
                    domain = expression.OR([[('parent_id', 'in', category_ids)], domain])
                else:
                    domain = expression.AND([[('parent_id', 'in', category_ids)], domain])
                for i in range(1, len(categories)):
                    domain = [[('name', operator, ' / '.join(categories[-1 - i:]))], domain]
                    if operator in expression.NEGATIVE_TERM_OPERATORS:
                        domain = expression.AND(domain)
                    else:
                        domain = expression.OR(domain)
            ids = self.search(cr, uid, expression.AND([domain, args]), limit=limit, context=context)
        else:
            ids = self.search(cr, uid, args, limit=limit, context=context)
        return self.name_get(cr, uid, ids, context)

    def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
        res = self.name_get(cr, uid, ids, context=context)
        return dict(res)


    name = fields.Char('name')
    seq = fields.Integer('sequence')
    task_ids = fields.One2many('project.task', 'categ_id')
    parent_id = fields.Many2one('task.category','Parent Category', select=True, ondelete='cascade')
    child_id = fields.One2many('task.category', 'parent_id', string='Child Categories')




class task(models.Model):
    _inherit = "project.task"


    @api.multi
    @api.depends('estimate_ids')
    def _compute_estimated_cost(self):

        for line in self:
            line.estimated_cost = 0.0
            for lines in line.estimate_ids:
                line.estimated_cost+=lines.estimated_cost_sum

    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_num = 1

        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context)
            line_num = 1
            for line_rec in first_line_rec.project_id.task_ids:
                line_rec.line_no = line_num
                line_num += 1
            line_num = 1
            for line_rec in first_line_rec.project_id.extra_task_ids:
                line_rec.line_no = line_num
                line_num += 1
            line_num = 1
            for line_rec in first_line_rec.project_id.temp_tasks:
                line_rec.line_no = line_num
                line_num += 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    estimated_cost = fields.Float(compute='_compute_estimated_cost', string='Estimated Cost')
    estimate_ids = fields.One2many('project.task.estimation', 'task_id', 'Estimation')
    is_extra_work = fields.Boolean('Extra Work', default=False)
    extra_id = fields.Many2one('project.project')
    partner_id = fields.Many2one(related='project_id.partner_id', string='Customer')
    usage_ids = fields.One2many(string='Items usage', related='estimate_ids')
    # stockpicking_ids = fields.One2many('stock.picking')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('inprogress', 'In Progress'),
        ('completed', 'Completed')
    ], default='draft')
    sub_categ_id = fields.Many2one('task.category', 'Sub Category')
    categ_id = fields.Many2one('task.category', 'Category')
    civil_contractor = fields.Many2one('res.partner', 'Civil Contractor', domain = [('contractor','=',True)])
    labour_report_ids = fields.One2many('project.labour.report', 'task_id')
    task_id2 = fields.Many2one('project.project', 'Project')


    @api.multi
    def task_approve(self):
        self.ensure_one()
        self.state = 'approved'

    @api.multi
    def start_task(self):
        self.ensure_one()
        self.state = 'inprogress'

    @api.multi
    def complete_task(self):
        self.ensure_one()
        # browse = self.env['stock.move']
        # search = self.env['stock.move'].search([('id','=',self.id)])
        # print 'self.id ',self.id, 'browse ',browse
        consumed_product_location = self.env.ref("hiworth_construction.stock_location_product_consumption").id
        # consumed_product_location = consumed_product_location_record.id
        move_lines = self.env['stock.picking'].search([('task_id','=',self.id)])
        if not move_lines:
            self.state = 'completed'
            return
        move_lines = move_lines[0].move_lines
        stock_picking_products = [(move.product_id, move.location_dest_id) for move in move_lines]
        # estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]

        res = {}
        Move = self.env['stock.move']
        for transfer in self.usage_ids:
            from_location = 12
            for stock_picking_product in stock_picking_products:
                if stock_picking_product[0] == transfer.pro_id:
                    from_location = stock_picking_product[1].id

            moves = self.env['stock.move']

            # Moving unused items back to stock
            move = Move.create({
                'name': transfer.pro_id.name,
                'product_id': transfer.pro_id.id,
                'restrict_lot_id': False,
                'product_uom_qty': (transfer.qty_assigned-transfer.qty_used),
                'product_uom': transfer.uom.id, #TODO: Change the test value 1 to produc_uom
                'partner_id': 1, #TODO: Change the test value 1 to partner_id
                'location_id': from_location,
                'location_dest_id': 12
            })
            moves |= move

            # Moving used quantity to 'Product Consumed' location
            if transfer.qty_used>0:
                move = Move.create({
                    'name': transfer.pro_id.name,
                    'product_id': transfer.pro_id.id,
                    'restrict_lot_id': False,
                    'product_uom_qty': transfer.qty_used,
                    'product_uom': transfer.uom.id, #TODO: Change the test value 1 to produc_uom
                    'partner_id': 1, #TODO: Change the test value 1 to partner_id
                    'location_id': from_location,
                    'location_dest_id': consumed_product_location
                })
                moves |= move

            res[transfer.id] = move.id
            moves.action_done()
        # products.write({'move_id': move.id, 'state': 'done'})

        self.state = 'completed'
        return res

    @api.multi
    def reset_task(self):
        self.ensure_one()
        self.state = 'draft'

class project_labour_report(models.Model):
    _name = 'project.labour.report'

    _order = "date asc"

    @api.multi
    @api.depends('labour_detail_ids')
    def _compute_amount(self):
        for line in self:
            line.amount = 0.0
            for lines in line.labour_detail_ids:
                line.amount+=lines.amount

    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_num = 1

        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context)
            for line_rec in first_line_rec.project_id.labour_report_ids:
                line_rec.line_no = line_num
                line_num += 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    name = fields.Text('Description')
    date = fields.Date('Date')
    amount = fields.Float(compute='_compute_amount', string='Amount')
    labour_detail_ids = fields.One2many('labour.details', 'detail_ids')
    task_id = fields.Many2one('project.task', 'Task')
    project_id = fields.Many2one('project.project', 'Project')


    _defaults = {
        'date': fields.Date.today(),
    }


class labour_details(models.Model):
    _name = 'labour.details'


    @api.multi
    @api.depends('product_id','rate','qty')
    def _compute_amount(self):

        for line in self:
            line.amount = line.rate * line.qty

    detail_ids = fields.Many2one('project.labour.report', 'Report')
    product_id = fields.Many2one('product.product', 'Product')
    rate = fields.Float(related='product_id.standard_price', string='Rate')
    qty = fields.Float('Nos')
    amount = fields.Float(compute='_compute_amount', string='Amount')



class category_items_estimation(models.Model):
    _name = 'category.items.estimation'

    @api.multi
    @api.depends('product_id','unit_price','qty')
    def _compute_amount(self):

        for line in self:
            line.amount = line.unit_price * line.qty

    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_num = 1

        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context)
            for line_rec in first_line_rec.project_id.categ_estimation_ids:
                line_rec.line_no = line_num
                line_num += 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    name = fields.Char('Name')
    product_id = fields.Many2one('product.product', 'Product')
    unit_price = fields.Float(related='product_id.standard_price', string="Unit Price")
    uom = fields.Many2one(related='product_id.uom_id', string="Uom")
    qty = fields.Float('Qty')
    amount = fields.Float(compute='_compute_amount', string='Amount')
    project_id = fields.Many2one('project.project', 'Project')




class project(models.Model):
    _inherit = "project.project"



    @api.multi
    @api.depends('task_ids')
    def _compute_estimated_cost(self):

        for line in self:
            for lines in line.task_ids:
                line.estimated_cost+=lines.estimated_cost
    @api.multi
    @api.depends('extra_task_ids')
    def _compute_estimated_cost_extra(self):

        for line in self:
            for lines in line.extra_task_ids:
                line.estimated_cost_extra+=lines.estimated_cost

    @api.multi
    @api.depends('estimated_cost','estimated_cost_extra')
    def _compute_estimated_cost_total(self):

        for line in self:
            line.total_estimated_cost = line.estimated_cost + line.estimated_cost_extra

    @api.onchange('schedule_id')
    @api.multi
    def _compute_stage_total(self):
        if (not self.schedule_id):
            return

        amount = 0.0
        for line in self.schedule_id:
            amount+= line.amount
        line['stage_total'] =  amount


    @api.multi
    @api.onchange('categ_id')
    def onchange_task_ids(self):
        return {
            'domain': {
                'task_ids':[('categ_id','=', self.categ_id.id)]
            }
        }


    @api.model
    def default_get(self, default_fields):
        vals = super(project, self).default_get(default_fields)
        user_ids =[]
        group_admin1 = self.env.ref('hiworth_project_management.group_admin1')
        if group_admin1:
            for user in group_admin1.users:
                if user.id not in user_ids:
                    user_ids.append(user.id)
        group_admin2 = self.env.ref('hiworth_project_management.group_admin2')
        if group_admin2:
            for user in group_admin2.users:
                if user.id not in user_ids:
                    user_ids.append(user.id)
        gm = self.env.ref('hiworth_project_management.group_general_manager')
        if gm:
            for user in gm.users:
                if user.id not in user_ids:
                    user_ids.append(user.id)
        vals['members'] = user_ids
        return vals

    # company_id = fields.Many2one('res.company', 'Company', required=True)
    estimated_cost = fields.Float(compute='_compute_estimated_cost', store=True, string='Estimated Cost')
    estimated_cost_extra = fields.Float(compute='_compute_estimated_cost_extra', store=True, string='Estimated Cost for Extra Work')
    total_estimated_cost = fields.Float(compute='_compute_estimated_cost_total', store=True, string='Total Estimated Cost')
    date_end = fields.Date('End Date')
    start_date = fields.Date('Start Date')
    user_id = fields.Many2one('res.users', 'Project Manager', default=False)
    task_ids = fields.One2many('project.task', 'project_id',
                               domain=[('is_extra_work', '=', False)])
    extra_task_ids = fields.One2many('project.task', 'project_id', domain=[('is_extra_work','=', True)])
    stage_id = fields.One2many('project.stages', 'project_id', 'Project Status')
    stages_generated = fields.Boolean('Stages Generated', default=False)
    location_id = fields.Many2one('stock.location', 'Location', domain=[('usage','=','internal')])
    cent = fields.Float('Cent')
    building_sqf = fields.Float('Building in Sq. Ft')
    rate = fields.Float('Rate')
    total_value = fields.Float('Total Value')
    schedule_id = fields.One2many('project.schedule', 'project_id', 'Schedule')
    schedule_note = fields.Text('Note')
    remark1 = fields.Char('Remarks')
    acc_statement = fields.One2many('account.move.line','project_id', string='Account Statement',compute="_onchange_acc_statement")
    acc_balance = fields.Float(string='Balance',compute="_onchange_acc_statement")
    civil_contractor = fields.Many2one('res.partner', 'Civil Contractor')
    project_product_ids = fields.One2many('project.product', 'project_id')
    labour_report_ids = fields.One2many('project.labour.report', 'project_id')
    categ_id = fields.Many2one('task.category', 'Category')
    view_categ_estimation = fields.Boolean('View Category Wise Estimation', default=False)
    hide_tasks = fields.Boolean('Hide Tasks', default=False)
    temp_tasks = fields.One2many('project.task', 'task_id2', 'Tasks')
    categ_estimation_ids = fields.One2many('category.items.estimation', 'project_id', 'Category Estimation')
    directory_ids = fields.One2many('project.directory', 'project_id', 'Directory')
    show_project_details=fields.Boolean()
    plot_details=fields.Boolean()
    permit_details=fields.Boolean()

    @api.model
    def get_ordered_records(self):
        # Fetch records sorted by 'year' in descending order
        ordered_records = self.search([], order='start_date desc')
        print(ordered_records, ' ordered_records ordered_records ordered_records ordered_records')
        return ordered_records

    @api.depends('company_id')
    def _onchange_company_id(self):
        if self.company_id:
            categ_id = self.env.ref('project.group_project_manager').id
            return {'domain':{'user_id':[('employee_id.branch_id','in',self.company_id.id),('employee_id.user_category','=',categ_id)]}}


    @api.depends('partner_id')
    def _onchange_acc_statement(self):
        debit = 0.0
        credit = 0.0
        record = self.env['account.move.line'].search([('project_id','=',self.id),('account_id','=',self.partner_id.property_account_receivable.id)])
        self.acc_statement = record
        for rec in record:
            debit += rec.debit
            credit += rec.credit
        self.acc_balance = debit - credit

    _defaults = {
        'schedule_note': 'KVAT AND SERVICE TAX AS PER GOVT. RULES SHOULD BE PAID IN ADDITION TO THE ABOVE AMOUNT ALONG WITH EACH INSTALLMENT. ALL INSTALLMENTS SHOULD BE PAID IN ADVANCE BEFORE STARTING EACH WORK',
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
    }



    @api.multi
    def compute_estimated_cost(self):
        temp=0.0
        for line in self:
            for lines in line.task_ids:
                temp+=lines.estimated_cost
            line.estimated_cost=temp
            temp2=0.0
            for lines in line.extra_task_ids:
                temp2 += lines.estimated_cost
            line.estimated_cost_extra=temp2


    @api.multi
    def display_project_status(self):
        stage_lines = self.env['project.stages.line'].search([('id','!=',False)])
        stage = self.env['project.stages']
        for line in self:
            if line.stages_generated == False:
                for stage_line in stage_lines:
                    values = {'stage_line_id': stage_line.id,
                              'state': 'no',
                              'project_id': line.id}
                    stage_id = stage.create(values)


            if line.stages_generated == True:

                for stage_line in stage_lines:
                    generated = False
                    for stages in stage_line.stage_id:
                        if stages.project_id.id == line.id:
                            generated = True
                    if generated ==  False:
                        values = {'stage_line_id': stage_line.id,
                                  'state': 'no',
                                  'project_id': line.id}
                        stage_id = stage.create(values)

                        line.stages_generated = True

            line.stages_generated = True


    @api.multi
    def visible_category(self):
        for line in self:
            line.view_categ_estimation=True

    @api.multi
    def hide_category(self):
        for line in self:
            line.view_categ_estimation = False
            line.hide_tasks = False

    @api.multi
    def refresh_category(self):
        for line in self:
            if line.categ_id.id == False:
                raise osv.except_osv(('Warning!'), ('Please Select A Category'))
            if line.categ_id.id != False:
                line.hide_tasks = True
                categ_estimation_obj = self.env['category.items.estimation']
                categ_estimations = categ_estimation_obj.search([('id','!=',False)])
                for items in categ_estimations:
                    items.unlink()

                temp_task_ids = self.env['project.task'].search([('task_id2','=',line.id)])
                for tasks2 in temp_task_ids:
                    tasks2.task_id2 = False

                child_ids = []
                childs=self.env['task.category'].search([('parent_id','=',line.categ_id.id)])
                for child in childs:
                    child_ids.append(child.id)
                if child_ids == []:
                    child_ids.append(line.categ_id.id)


                task_ids = self.env['project.task'].search([('project_id','=',line.id),('categ_id','in',child_ids)])
                for lines in task_ids:
                    lines.task_id2 = line.id
                    for esimations in lines.estimate_ids:
                        if categ_estimation_obj.search([('product_id','=',esimations.pro_id.id)]).id != False:
                            categ_obj = categ_estimation_obj.search([('product_id','=',esimations.pro_id.id)])
                            categ_obj.qty+=esimations.qty
                        if categ_estimation_obj.search([('product_id','=',esimations.pro_id.id)]).id == False:
                            values = {'product_id':esimations.pro_id.id,
                                      'qty':esimations.qty,
                                      'project_id':line.id}
                            categ_estimation_obj.create(values)

    @api.model
    def get_records(self, project_id):

        res = self.env['project.labour.report'].search([('project_id','=',project_id)])
        recordset = res.sorted(key=lambda r: r.date)
        return recordset

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        return res


class document_file(models.Model):
    _inherit = 'ir.attachment'

    ref_name = fields.Char('Description', size=100)
    stage_id = fields.Many2one('project.stages', 'Project Stage')
    att_ids = fields.Many2one('im_chat.message.req', )
    project_image = fields.Many2one('project.project')
    gallery_img = fields.Many2one('gallery.project')
    gallery = fields.Boolean(default=False)
    drawing_id = fields.Many2one('project.project')


class project_attachment(models.Model):
    _name = 'project.attachment'
    _description = "Project Attachment"

    name = fields.Char('Name')
    binary_field = fields.Binary('File')
    filename = fields.Char('Filename')
    parent_id = fields.Many2one('document.directory', 'Directory')
    stage_id = fields.Many2one('project.stages', 'Project Stage')
    project_id = fields.Many2one(related='stage_id.project_id', string="Project")


class project_directory(models.Model):
    _name = 'project.directory'

    name = fields.Char('Name')
    project_id = fields.Many2one('project.project', 'Project')
    directory_id = fields.Many2one('document.directory', 'Directories')

    @api.multi
    def open_selected_directory(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['document.directory'].search([('id','=',self.directory_id.id)])

        context = self._context.copy()
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Directory Form view',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'document.directory',
            'view_id':'view_document_directory_form',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }
class document_directory(models.Model):
    _inherit = 'document.directory'

    @api.multi
    @api.depends('parent_id')
    def _compute_is_parent(self):
        for line in self:
            if line.parent_id.id == False:
                line.is_parent = True
            if line.parent_id.id != False:
                line.is_parent = False

    pro_attachment_ids = fields.One2many('project.attachment', 'parent_id', 'Attachments')
    is_parent = fields.Boolean(compute='_compute_is_parent', store=True, readonly=False, string="Parent")

class project_stages(models.Model):
    _name = 'project.stages'
    _order = "sequence, id"

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
    project_id = fields.Many2one('project.project', 'Project')
    stage_line_id = fields.Many2one('project.stages.line', 'Stage')
    attachment_id = fields.One2many('project.attachment', 'stage_id', 'Attachments')
    state = fields.Selection([('no', 'No'),('yes', 'Yes')], 'Status',
                             select=True, copy=False)
    seq = fields.Integer(related='stage_line_id.seq', store=True, string='Sequence')

    _defaults = {
        'state': 'no'}

class project_schedule(models.Model):
    _name = 'project.schedule'
    _order = "seq asc"

    @api.multi
    @api.depends('amount')
    def _compute_stage_total(self):
        for line in self:
            for lines in line.project_id.schedule_id:
                if lines.seq <= line.seq:
                    line.stage_total += lines.amount

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
    seq = fields.Integer('Seq')
    amount = fields.Float('Inst Amount')
    due_on = fields.Char('Due on')
    stage_total = fields.Float(compute='_compute_stage_total',  store=True, string='Stage Total')
    payment_stage = fields.Char('Payment Stage')
    date = fields.Date('Date')
    project_id = fields.Many2one('project.project', 'Project')
    remarks = fields.Char('Remarks')

class supervision_schedule(models.Model):

    _name = 'supervision.project.schedule'
    _order = "seq asc"

    @api.multi
    @api.depends('amount')
    def _compute_stage_total(self):
        for line in self:
            for lines in line.project_id.schedule_id:
                if lines.seq <= line.seq:
                    line.stage_total += lines.amount

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
    seq = fields.Integer('Seq')
    amount = fields.Float('Inst Amount')
    due_on = fields.Char('Due on')
    stage_total = fields.Float(compute='_compute_stage_total', store=True, string='Stage Total')
    payment_stage = fields.Char('Payment Stage')
    date = fields.Date('Date')
    project_id = fields.Many2one('project.project', 'Project')
    remarks = fields.Char('Remarks')

class project_stages_line(models.Model):
    _name = 'project.stages.line'

    _order = "seq asc"


    name = fields.Char('Status')
    seq = fields.Integer('Sequence')
    stage_id = fields.One2many('project.stages', 'stage_line_id', 'Stages')
class project_task_estimation(models.Model):
    _name = 'project.task.estimation'

    @api.multi
    @api.depends('pro_id','qty','unit_price')
    def _compute_estimated_cost_sum(self):

        for line in self:
            line.estimated_cost_sum = line.qty * line.unit_price

    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_num = 1

        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context)
            for line_rec in first_line_rec.task_id.estimate_ids:
                line_rec.line_no = line_num
                line_num += 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    name = fields.Char('Description')
    task_id = fields.Many2one('project.task', 'Task')
    project_id = fields.Many2one(related='task_id.project_id', string="Project")
    pro_id =  fields.Many2one('product.product', 'Resource')
    qty = fields.Float('Qty', default=1)
    unit_price = fields.Float(related='pro_id.standard_price', string='Unit Price')
    uom = fields.Many2one(related='pro_id.uom_id',string='Uom')
    estimated_cost_sum =  fields.Float(compute='_compute_estimated_cost_sum', string='Estimated Cost')
    qty_used = fields.Float('Consumed Qty', default=0)
    qty_assigned = fields.Float(compute='_compute_qty_assigned', string='Assigned quantity')
    trigger_project_estimation_calc = fields.Integer(compute='_trigger_project_estimation_calc')
    invoiced_qty = fields.Float('Invoiced Qty', default=0.0)


    @api.multi
    @api.depends('qty')
    def _trigger_project_estimation_calc(self):
        # Retrive all product ids related to current project and delete from project_product table
        project_product_recs_ids = self.env['project.product'].search([('project_id','=',self[0].task_id.project_id.id)])._ids
        if project_product_recs_ids:
            sql = ('DELETE FROM project_product '
                   'WHERE id in {}').format('('+', '.join(str(t) for t in project_product_recs_ids)+')')
            self.env.cr.execute(sql)

        project = self.env['project.project'].browse(self[0].task_id.project_id.id)

        project_product_list = []
        prod_dict = {}

        for task in project.task_ids:
            for estimate in task.estimate_ids:
                if estimate.pro_id not in prod_dict:
                    prod_dict[estimate.pro_id] = estimate.qty
                else:
                    prod_dict[estimate.pro_id] = prod_dict[estimate.pro_id]+estimate.qty

        for key, value in prod_dict.items():
            project_product_dict = {}
            project_product_dict['name'] = key.id
            project_product_dict['quantity'] = value
            project_product_dict['unit_price'] = key.standard_price
            project_product_dict['estimated_price'] = value*key.standard_price
            project_product_dict['project_id'] = project.id
            project_product_list.append(project_product_dict)
        for rec in project_product_list:
            self.env['project.product'].create(rec)

    @api.multi
    @api.depends('pro_id')
    def _compute_qty_assigned(self):
        for line in self:
            stock_picking = self.env['stock.picking'].search([('task_id','=',line.task_id.id),('state','=','done')])
            if not stock_picking:
                line.qty_assigned = 0
                return
            stock_picking = stock_picking[0]
            for move_line in stock_picking.move_lines:
                if move_line.product_id==line.pro_id:
                    line.qty_assigned = move_line.product_uom_qty

    @api.onchange('qty_used')
    @api.multi
    def _restrict_qty_used(self):
        if self.qty_used>self.qty_assigned:
            self.qty_used=0
            return {
                'warning': {
                    'title': 'Warning',
                    'message': "Used qunatity cannot be greater than assigned quantity."
                }
            }

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.multi
    @api.depends('name')
    def _get_opposite_accounts_cash_bank(self):
        for temp in self:
            temp.opp_acc_cash_bank = ""
            for line in temp.move_id:
                for lines in line.line_id:
                    if lines.id != temp.id:
                        if lines.account_id.is_cash_bank == True:
                            temp.opp_acc_cash_bank = lines.account_id.name + "," + temp.opp_acc_cash_bank

    description2 =  fields.Char('Description')
    project_id = fields.Many2one('project.project', 'Project')
    opp_acc_cash_bank = fields.Char(compute='_get_opposite_accounts_cash_bank', store=True, string='Account Opposite')



class account_voucher(models.Model):
    _inherit = 'account.voucher'


    description =  fields.Char('Description')

    def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
        '''
        Return a dict to be use to create the first account move line of given voucher.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param move_id: Id of account move where this line will be added.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
        if voucher.type in ('purchase', 'payment'):
            credit = voucher.paid_amount_in_company_currency
        elif voucher.type in ('sale', 'receipt'):
            debit = voucher.paid_amount_in_company_currency
        if debit < 0: credit = -debit; debit = 0.0
        if credit < 0: debit = -credit; credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        move_line = {
            'name': voucher.name or '/',
            'debit': debit,
            'credit': credit,
            'account_id': voucher.account_id.id,
            'move_id': move_id,
            'journal_id': voucher.journal_id.id,
            'period_id': voucher.period_id.id,
            'partner_id': voucher.partner_id.id,
            'currency_id': company_currency <> current_currency and  current_currency or False,
            'amount_currency': (sign * abs(voucher.amount) # amount < 0 for refunds
                                if company_currency != current_currency else 0.0),
            'date': voucher.date,
            'date_maturity': voucher.date_due,
            'description2': voucher.description
        }
        return move_line


    def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
        '''
        Set a dict to be use to create the writeoff move line.

        :param voucher_id: Id of voucher what we are creating account_move.
        :param line_total: Amount remaining to be allocated on lines.
        :param move_id: Id of account move where this line will be added.
        :param name: Description of account move line.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: mapping between fieldname and value of account move line to create
        :rtype: dict
        '''
        currency_obj = self.pool.get('res.currency')
        move_line = {}

        voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
        current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id

        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
            diff = line_total
            account_id = False
            write_off_name = ''
            if voucher.payment_option == 'with_writeoff':
                account_id = voucher.writeoff_acc_id.id
                write_off_name = voucher.comment
            elif voucher.partner_id:
                if voucher.type in ('sale', 'receipt'):
                    account_id = voucher.partner_id.property_account_receivable.id
                else:
                    account_id = voucher.partner_id.property_account_payable.id
            else:
                # fallback on account of voucher
                account_id = voucher.account_id.id
            sign = voucher.type == 'payment' and -1 or 1
            move_line = {
                'name': write_off_name or name,
                'account_id': account_id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'date': voucher.date,
                'credit': diff > 0 and diff or 0.0,
                'debit': diff < 0 and -diff or 0.0,
                'amount_currency': company_currency <> current_currency and (sign * -1 * voucher.writeoff_amount) or 0.0,
                'currency_id': company_currency <> current_currency and current_currency or False,
                'analytic_account_id': voucher.analytic_id and voucher.analytic_id.id or False,
                'description2': voucher.description
            }

        return move_line


    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            local_context = dict(context, force_company=voucher.journal_id.company_id.id)
            if voucher.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, voucher.id, context)
            current_currency = self._get_current_currency(cr, uid, voucher.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, voucher.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': voucher.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the voucher
            print 'lines======================================', self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context)
            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context), local_context)
            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
            line_total = move_line_brw.debit - move_line_brw.credit
            rec_list_ids = []
            if voucher.type == 'sale':
                line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            elif voucher.type == 'purchase':
                line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
            # Create one move line per voucher line where amount is not 0.0
            line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)

            # Create the writeoff line if needed
            ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
            print 'ml_writeoff====================================', ml_writeoff
            if ml_writeoff:
                move_line_pool.create(cr, uid, ml_writeoff, local_context)
            # We post the voucher.
            self.write(cr, uid, [voucher.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            if voucher.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
            # We automatically reconcile the account move lines.
            reconcile = False
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
        return True


    def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
        '''
        Create one account move line, on the given account move, per voucher line where amount is not 0.0.
        It returns Tuple with tot_line what is total of difference between debit and credit and
        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).

        :param voucher_id: Voucher id what we are working with
        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
        :param move_id: Account move wher those lines will be joined.
        :param company_currency: id of currency of the company to which the voucher belong
        :param current_currency: id of currency of the voucher
        :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
        :rtype: tuple(float, list of int)
        '''
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        currency_obj = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        tot_line = line_total
        rec_lst_ids = []

        date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
        ctx = context.copy()
        ctx.update({'date': date})
        voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
        voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
        ctx.update({
            'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
            'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
        prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
        for line in voucher.line_ids:
            #create one move line per voucher line where amount is not 0.0
            # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
            if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
                continue
            # convert the amount set on the voucher line into the currency of the voucher's company
            # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
            # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
            # currency rate difference
            if line.amount == line.amount_unreconciled:
                if not line.move_line_id:
                    raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
                sign = line.type =='dr' and -1 or 1
                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
            else:
                currency_rate_difference = 0.0
            move_line = {
                'journal_id': voucher.journal_id.id,
                'period_id': voucher.period_id.id,
                'name': line.name or '/',
                'account_id': line.account_id.id,
                'move_id': move_id,
                'partner_id': voucher.partner_id.id,
                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                'quantity': 1,
                'credit': 0.0,
                'debit': 0.0,
                'date': voucher.date,
                'description2': voucher.description
            }
            if amount < 0:
                amount = -amount
                if line.type == 'dr':
                    line.type = 'cr'
                else:
                    line.type = 'dr'

            if (line.type=='dr'):
                tot_line += amount
                move_line['debit'] = amount
            else:
                tot_line -= amount
                move_line['credit'] = amount

            if voucher.tax_id and voucher.type in ('sale', 'purchase'):
                move_line.update({
                    'account_tax_id': voucher.tax_id.id,
                })

            # compute the amount in foreign currency
            foreign_currency_diff = 0.0
            amount_currency = False
            if line.move_line_id:
                # We want to set it on the account move line as soon as the original line had a foreign currency
                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
                    # we compute the amount in that foreign currency.
                    if line.move_line_id.currency_id.id == current_currency:
                        # if the voucher and the voucher line share the same currency, there is no computation to do
                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                        amount_currency = sign * (line.amount)
                    else:
                        # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
                        # otherwise we use the rates of the system
                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
                if line.amount == line.amount_unreconciled:
                    foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)

            move_line['amount_currency'] = amount_currency
            voucher_line = move_line_obj.create(cr, uid, move_line)
            rec_ids = [voucher_line, line.move_line_id.id]

            if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
                # Change difference entry in company currency
                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
                move_line_obj.create(cr, uid, exch_lines[1], context)
                rec_ids.append(new_id)

            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
                # Change difference entry in voucher currency
                move_line_foreign_currency = {
                    'journal_id': line.voucher_id.journal_id.id,
                    'period_id': line.voucher_id.period_id.id,
                    'name': _('change')+': '+(line.name or '/'),
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': line.voucher_id.partner_id.id,
                    'currency_id': line.move_line_id.currency_id.id,
                    'amount_currency': (-1 if line.type == 'cr' else 1) * foreign_currency_diff,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': line.voucher_id.date,

                }
                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
                rec_ids.append(new_id)
            if line.move_line_id.id:
                rec_lst_ids.append(rec_ids)
        return (tot_line, rec_lst_ids)


class purchase_order(models.Model):
    _inherit = 'purchase.order'

    READONLY_STATES = {
        'confirmed': [('readonly', True)],
        'approved': [('readonly', True)],
        'done': [('readonly', True)]
    }

    @api.multi
    @api.depends('name')
    def _count_invoices(self):
        for line in self:
            line.invoice_count = 0
            invoice_ids = self.env['hiworth.invoice'].search([('origin','=',line.name)])
            line.invoice_count = len(invoice_ids)

    STATE_SELECTION = [
        ('draft', 'Waiting'),
        ('sanction', 'Sanctioned'),
        ('sent', 'RFQ'),
        ('bid', 'Bid Received'),
        ('confirmed', 'Waiting Approval'),
        ('approved', 'Order Placed'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Received'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
    ]

    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
                             help="The status of the purchase order or the quotation request. "
                                  "A request for quotation is a purchase order in a 'Draft' status. "
                                  "Then the order has to be confirmed by the user, the status switch "
                                  "to 'Confirmed'. Then the supplier must confirm the order to change "
                                  "the status to 'Approved'. When the purchase order is paid and "
                                  "received, the status becomes 'Done'. If a cancel action occurs in "
                                  "the invoice or in the receipt of goods, the status becomes "
                                  "in exception.",
                             select=True, copy=False)



    partner_id = fields.Many2one('res.partner', 'Supplier', required=False, states=READONLY_STATES,
                                 change_default=True, track_visibility='always')
    invoice_created = fields.Boolean('Invoice Created', default=False)
    invoice_count = fields.Integer(compute='_count_invoices', string='Invoice Nos')
    order_line = fields.One2many('purchase.order.line', 'order_id', 'Order Lines',
                                 states={'paid':[('readonly',True)]},
                                 copy=True)
    is_requisition = fields.Boolean('Is Requisition', default = True)
    requisition_id = fields.Many2one('purchase.order', 'Purchase Requisition')

    def wkf_send_rfq(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        #         print 'qqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq'
        if not context:
            context= {}
        ir_model_data = self.pool.get('ir.model.data')
        try:
            if context.get('send_rfq', False):
                #                 print 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
                template_id = ir_model_data.get_object_reference(cr, uid, 'hiworth_construction', 'email_template_edi_purchase15')[1]
            else:
                #                 print'ccccccccccccccccccccccccccccccc'
                template_id = ir_model_data.get_object_reference(cr, uid, 'hiworth_construction', 'email_template_edi_purchase_done2')[1]
        except ValueError:
            template_id = False
        try:
            #             print 'aaaaaaqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqqq'
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }



    def picking_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'shipped':1,'state':'done'}, context=context)
        # Do check on related procurements:
        proc_obj = self.pool.get("procurement.order")
        po_lines = []
        for po in self.browse(cr, uid, ids, context=context):
            po_lines += [x.id for x in po.order_line if x.state != 'cancel']
        if po_lines:
            procs = proc_obj.search(cr, uid, [('purchase_line_id', 'in', po_lines)], context=context)
            if procs:
                proc_obj.check(cr, uid, procs, context=context)
        self.message_post(cr, uid, ids, body=_("Products received"), context=context)
        return True

    @api.multi
    def create_invoice(self):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        if not self.partner_ref:
            raise osv.except_osv(_('Warning!'),
                                 _('You must enter a Invoice Number'))

        invoice_line = self.env['hiworth.invoice.line2']
        invoice = self.env['hiworth.invoice']
        now = datetime.datetime.now()
        for line in self:
            values1 = {
                'is_purchase_bill': True,
                'partner_id': line.partner_id.id,
                'purchase_order_date':line.date_order,
                'origin': line.name,
                'name': "INV/" + self.partner_ref +"/" + self.name +"/" + str(now.year)
                #                         'grand_total': line.amount_total
            }
            invoice_id = invoice.create(values1)
            for lines in line.order_line:
                values2={
                    'product_id': lines.product_id.id,
                    'name': lines.product_id.name,
                    'price_unit': lines.price_unit,
                    'uos_id': lines.product_uom.id,
                    'quantity': lines.product_qty,
                    'price_subtotal':lines.price_subtotal,
                    'task_id': lines.task_id.id,
                    'location_id': lines.location_id.id,
                    'invoice_id': invoice_id.id,
                }
                invoice_line_id = invoice_line.create(values2)
            invoice_id.action_for_approval()
            invoice_id.action_approve()
            line.invoice_created = True

    @api.multi
    def action_sanction(self):
        for line in self:
            line.state = 'sanction'

    @api.multi
    def invoice_open(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['hiworth.invoice'].search([('origin','=',self.name)])

        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Invoice view',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'hiworth.invoice',
            'view_id':'hiworth_invoice_form',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }


class invoice_attachment(models.Model):
    _name = "invoice.attachment"

    @api.onchange('parent_id')
    def _onchange_attachment_selection(self):
        res={}
        attachment_ids = []
        if self.parent_id.id != False and self.invoice_id.project_id.id != False:
            attachment_ids = [attachment.id for attachment in self.env['project.attachment'].search([('parent_id','=',self.parent_id.id),('project_id','=',self.invoice_id.project_id.id)])]
            return {
                'domain': {
                    'attachment_id': [('id','in',attachment_ids)]
                }
            }
        if self.parent_id.id != False and self.invoice_id.project_id.id == False:
            attachment_ids = [attachment.id for attachment in self.env['project.attachment'].search([('parent_id','=',self.parent_id.id)])]
            return {
                'domain': {
                    'attachment_id': [('id','in',attachment_ids)]
                }
            }
        else:
            return res

    name = fields.Char('Name')
    attachment_id = fields.Many2one('project.attachment', 'Attachments')
    filename = fields.Char(related='attachment_id.filename', string='Filename')
    binary_field = fields.Binary(related='attachment_id.binary_field', string="File")
    invoice_id = fields.Many2one('account.invoice', 'Invoice')
    parent_id = fields.Many2one('document.directory', 'Directory')

class account_invoice(models.Model):
    _inherit = "account.invoice"
    _rec_name = 'prime_invoice'


    @api.onchange('project_id')
    def _onchange_task_selection(self):
        if self.is_contractor_bill == True:
            return {
                'domain': {
                    'task_id': [('project_id','=',self.project_id.id)]
                }
            }


    @api.onchange('is_contractor_bill')
    def _onchange_contractor_selection(self):
        if self.is_contractor_bill == True:
            return {
                'domain': {
                    'partner_id': [('contractor','=',True)]
                }
            }

    @api.multi
    @api.depends('task_id')
    def _visible_prevoius_bills(self):

        for line in self:
            #             print 'task_id ==============================', line.task_id
            if line.task_id.id != False:
                line.visible_previous_bill = True

    @api.multi
    @api.depends('amount_total','residual')
    def _compute_balance(self):
        for line in self:
            #             print 'task_id ==============================', line.task_id
            if line.state == 'draft':
                line.balance2 = line.amount_total
            if line.state != 'draft':
                line.balance2 = line.residual

    @api.multi
    @api.depends('prevous_bills')
    def _compute_prevoius_balance(self):
        for line in self:
            for lines in line.prevous_bills:
                line.previous_balance+=lines.balance2

    @api.multi
    @api.depends('previous_balance','amount_total','residual')
    def _compute_net_total(self):
        for line in self:
            if line.residual == 0.0:
                line.net_total = line.previous_balance + line.amount_total
            else:
                line.net_total = line.previous_balance + line.residual

    state = fields.Selection([
        ('draft','Draft'),
        ('proforma','Pro-forma'),
        ('proforma2','Pro-forma'),
        ('open','Waiting for Approval'),
        ('approve','Approved'),
        ('paid','Paid'),
        ('cancel','Cancelled'),
    ], string='Status', index=True, readonly=True, default='draft',
        track_visibility='onchange', copy=False,
        help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
             " * The 'Pro-forma' when invoice is in Pro-forma status,invoice does not have an invoice number.\n"
             " * The 'Open' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice.\n"
             " * The 'Approved' status is used when the Invoice approved for Payment.\n"
             " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
             " * The 'Cancelled' status is used when user cancel invoice.")
    project_id = fields.Many2one('project.project', 'Project')
    customer_id = fields.Many2one(related='project_id.partner_id', string="Client")
    is_contractor_bill = fields.Boolean('Contractor Bill', default=False)
    task_id = fields.Many2one('project.task', 'Task')
    prevous_bills = fields.One2many('account.invoice', 'invoice_id5', 'Previous Invoices')
    invoice_id5 = fields.Many2one('account.invoice', 'Invoices')
    visible_previous_bill = fields.Boolean(compute='_visible_prevoius_bills', store=True, string="Visible Prevoius Bill", default=False)
    visible_bills = fields.Boolean('Visible', default=False)
    balance2 = fields.Float(compute='_compute_balance', string="Balance Of Not Validated")
    previous_balance = fields.Float(compute='_compute_prevoius_balance', string="Previous Balance")
    net_total = fields.Float(compute='_compute_net_total', string="Net Total")
    attachment_ids = fields.One2many('invoice.attachment', 'invoice_id', 'Attachments')
    task_related = fields.Boolean('Related To Task')
    agreed_amount = fields.Float(related='task_id.estimated_cost', string="Agreement Amount")
    type_id = fields.Selection([('Arch','Architectural'),('Struc','Structural'),('Super','Supervision')],string="Type",required=True)
    prime_invoice = fields.Char('Prime Invoice')

    #     attachment_ids = fields.Many2one('project.attachment', 'Attachments')


    @api.multi
    def refresh_prevoius_bills(self):
        for line in self:
            #             print 'lines33333333333333333333333333333', line.task_id
            invoice_objs = self.env['account.invoice'].search([('task_id','=',line.task_id.id)])

            for invoice in invoice_objs:
                invoice.invoice_id5 = False
            #                 print 'test====================='
            for invoices in invoice_objs:
                if invoices.id != line.id:
                    invoices.invoice_id5 = line.id
            #                 print 'test===================',invoices.invoice_id5
            line.visible_bills = True

    @api.multi
    def hide_prevoius_bills(self):
        for line in self:
            line.visible_bills = False

    @api.multi
    def invoice_approve(self):
        for line in self:
            line.state = 'approve'


#     @api.multi
#     def action_invoice_sent(self):
#         """ Open a window to compose an email, with the edi invoice template
#             message loaded by default
#         """
#         assert len(self) == 1, 'This option should only be used for a single id at a time.'
#         template = self.env.ref('hiworth_construction.email_template_edi_invoice23', False)
#         compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
# #         print 'template=====================23423423234====', template
#         ctx = dict(
#             default_model='account.invoice',
#             default_res_id=self.id,
#             default_use_template=bool(template),
#             default_template_id=template.id,
#             default_composition_mode='comment',
#             mark_invoice_as_sent=True,
#         )
# #         print 'sdfsdfsdfsdfsdfsdfsdfsdfsfsdf445645645'
#         return {
#             'name': _('Compose Email'),
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'mail.compose.message',
#             'views': [(compose_form.id, 'form')],
#             'view_id': compose_form.id,
#             'target': 'new',
#             'context': ctx,
#         }




class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'

    @api.onchange('quantity')
    def _onchange_qty(self):
        if self.product_id.id != False and self.quantity != 0:
            task_id = self.invoice_id.task_id
            #             print 'task_id===================', self.invoice_id,self.invoice_id.task_id

            estimation = self.env['project.task.estimation'].search([('task_id','=',task_id.id),('pro_id','=',self.product_id.id)])
            #             print 'estimation========================', estimation
            if estimation.invoiced_qty == 0.0:
                if estimation.qty == 0.0:
                    self.quantity = 0.0
                    return {
                        'warning': {
                            'title': 'Warning',
                            'message': "Please enter some Qty in the Estimation."
                        }
                    }
                if estimation.qty < self.quantity:
                    self.quantity = estimation.qty
                    #                     estimation.write({'invoiced_qty': self.quantity})
                    return {
                        'warning': {
                            'title': 'Warning',
                            'message': "Entered qty is greater than the qty to invoice."
                        }
                    }
                if estimation.qty > self.quantity:
                    print 'qweqeqweqeqwe'
            #                     estimation.write({'invoiced_qty': self.quantity})
            #                 print 'estimation=======================', estimation,estimation.invoiced_qty
            if estimation.invoiced_qty != 0.0:
                if self.quantity > estimation.qty - estimation.invoiced_qty:
                    self.quantity = estimation.qty - estimation.invoiced_qty
                    #                     print 'asdasd========================', self.quantity
                    return {
                        'warning': {
                            'title': 'Warning',
                            'message': "Entered qty is greater than the qty to invoice."
                        }
                    }



    #     task_id = fields.Many2one('project.task', string='task',
    #         related='invoice_id.task_id', store=True, readonly=True)
    #     task_related = fields.Boolean(related='invoice_id.task_related', store=True, string='Related To Task')
    total_assigned_qty = fields.Float('Assigned Qty')
    discount_amt = fields.Float('Cash Discount')
    net_total = fields.Float('Net Total')

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
                          partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
                          company_id=None, task_related=False,task_id=False):
        context = self._context
        company_id = company_id if company_id is not None else context.get('company_id', False)
        self = self.with_context(company_id=company_id, force_company=company_id)

        if not partner_id:
            raise except_orm(_('No Partner Defined!'), _("You must first select a partner!"))

        values = {}

        part = self.env['res.partner'].browse(partner_id)
        fpos = self.env['account.fiscal.position'].browse(fposition_id)

        if part.lang:
            self = self.with_context(lang=part.lang)
        product = self.env['product.product'].browse(product)

        values['name'] = product.partner_ref
        if type in ('out_invoice', 'out_refund'):
            account = product.property_account_income or product.categ_id.property_account_income_categ
        else:
            account = product.property_account_expense or product.categ_id.property_account_expense_categ
        account = fpos.map_account(account)
        if account:
            values['account_id'] = account.id

        if type in ('out_invoice', 'out_refund'):
            taxes = product.taxes_id or account.tax_ids
            if product.description_sale:
                values['name'] += '\n' + product.description_sale
        else:
            taxes = product.supplier_taxes_id or account.tax_ids
            if product.description_purchase:
                values['name'] += '\n' + product.description_purchase

        fp_taxes = fpos.map_tax(taxes)
        values['invoice_line_tax_id'] = fp_taxes.ids

        if type in ('in_invoice', 'in_refund'):
            if price_unit and price_unit != product.standard_price:
                values['price_unit'] = price_unit
            else:
                values['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.standard_price, taxes, fp_taxes.ids)
        else:
            values['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.lst_price, taxes, fp_taxes.ids)

        values['uos_id'] = product.uom_id.id
        if uom_id:
            uom = self.env['product.uom'].browse(uom_id)
            if product.uom_id.category_id.id == uom.category_id.id:
                values['uos_id'] = uom_id

        domain = {'uos_id': [('category_id', '=', product.uom_id.category_id.id)]}

        company = self.env['res.company'].browse(company_id)
        currency = self.env['res.currency'].browse(currency_id)

        if company and currency:
            if company.currency_id != currency:
                values['price_unit'] = values['price_unit'] * currency.rate

            if values['uos_id'] and values['uos_id'] != product.uom_id.id:
                values['price_unit'] = self.env['product.uom']._compute_price(
                    product.uom_id.id, values['price_unit'], values['uos_id'])

        #         print 'parpartner_ident ========================', partner_id,task_related,task_id,product
        product_ids = []
        if task_related == True:
            print 'test======================',task_id,product
            estimation = self.env['project.task.estimation'].search([('task_id','=',task_id),('pro_id','=',product.id)])
            values['total_assigned_qty']=estimation.qty
            values['quantity']=0.0
            if task_id == False:
                raise osv.except_osv(_('Warning!'),
                                     _('Please enter a task or uncheck "Related to task Field"'))
            if task_id != False:
                #                 print 'task=============================', self.env['project.task'].search([('id','=',task_id)])
                product_ids = [estimate.pro_id.id for estimate in self.env['project.task'].search([('id','=',task_id)]).estimate_ids]
                return {'value': values, 'domain': {'product_id': [('id','in',product_ids)]}}

        if not product:
            if type in ('in_invoice', 'in_refund'):
                return {'value': {}, 'domain': {'uos_id': []}}
            else:
                return {'value': {'price_unit': 0.0}, 'domain': {'uos_id': []}}

        return {'value': values, 'domain': domain,}


    @api.model
    def create(self,vals):
        #         task_id = self.invoice_id.task_id
        #         print 'vals======================', vals
        if 'invoice_id' in vals:
            task_id = self.env['account.invoice'].browse(vals['invoice_id']).task_id
            product_id = self.env['product.product'].browse(vals['product_id'])
            estimation = self.env['project.task.estimation'].search([('task_id','=',task_id.id),('pro_id','=',product_id.id)])
            print 'estimation==================',task_id ,estimation
            if vals['quantity'] != 0.0:
                estimation.write({'invoiced_qty': estimation.invoiced_qty+vals['quantity']})
            vals['total_assigned_qty']=estimation.qty
            return super(account_invoice_line, self).create(vals)
        return super(account_invoice_line, self).create(vals)

#     @api.model
#     def write(self,vals):
#
#         if vals['quantity']:
#             task_id = self.env['account.invoice'].browse(vals['invoice_id']).task_id
#             product_id = self.env['product.product'].browse(vals['product_id'])
#             estimation = self.env['project.task.estimation'].search([('task_id','=',task_id.id),('pro_id','=',product_id.id)])
#
#
#
#         super(account_invoice_line, self).write(vals)
#         return True


class product_cost_table(models.Model):
    _name = "product.cost.table"

    _order = "date desc"

    name = fields.Char('name')
    product_id = fields.Many2one('product.template', 'Product')
    date = fields.Date('Date')
    standard_price = fields.Float('Cost')
    purchase_id = fields.Char('Reference')
    remarks = fields.Char('Remarks' ,size=200)
#   template_id = fields.Many2one('product.template', 'Product Tempate')

#
# class product_product(models.Model):
#     _inherit = "product.product"
#
#     @maulti
#     @depends('name')
#     def _total_product_in(self, cr, uid, ids, field_names=None, arg=False, context=None):
#         context = context or {}
#         field_names = field_names or []
#
# #         domain_products = [('product_id', 'in', ids)]
# #         domain_quant, domain_move_in, domain_move_out = [], [], []
#         domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations(cr, uid, ids, context=context)
#         print 'qqqqqqqqqqqqqqqqqqq=================',domain_move_in_loc,asdasd
# #         domain_move_in += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
# #         domain_move_out += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
# #         domain_quant += domain_products
#     total_qty_received = fields.Float(compute='__total_product_in', string="Total Qty In")



class product_template(models.Model):
    _inherit = "product.template"

    #     @api.multi
    #     @api.depends('standard_price','cost_table_id')
    #     def _compute_old_price(self):
    #
    #         for line in self:
    #             cost_table = []
    #             cost_table = [table.id for table in line.cost_table_id]
    #             if len(cost_table) == 0:
    #                 print 'test==========================21221'
    #                 line.old_price = line.standard_price
    #
    #             print 'iefsdf===============================', len(cost_table)
    #             if len(cost_table) > 1:
    #                 tables = self.env['product.cost.table'].search([('id','in',cost_table)])
    #                 recordset = tables.sorted(key=lambda r: r.date, reverse=True)
    #                 line.old_price = recordset[1].standard_price
    #                 line.standard_price = recordset[0].standard_price
    #                 print 'test==========================21221',tables,recordset,recordset[1],recordset[0],recordset[0]
    # #             for costs in line.cost_table_id:
    # #                 print 'cost_tables============================',line.cost_table_id,line.id,len(line.cost_table_id.search([('product_id','=',line.id)]))
    # #                 if len(line.cost_table_id.search([('product_id','=',line.id)])) > 1:
    # #                     pre_id = line.cost_table_id.search([('product_id','=',line.id)])[len(line.cost_table_id.search([('product_id','=',line.id)]))-1].standard_price
    # #                     print 'pre_id==========================', pre_id
    # #                     line.old_price = pre_id
    # # #                 line.old_price = line.standard_price
    # #             if cost_table == []:


    @api.multi
    @api.depends('standard_price','qty_available')
    def _compute_inventory_value(self):

        for line in self:
            line.inventory_value = line.standard_price * line.qty_available

    @api.multi
    @api.depends('name')
    def _compute_total_in_qty(self):
        cr = self._cr
        uid = self._uid
        context = self._context
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        warehouse = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', user.company_id.id)], limit=1, context=context)
        loc_id = self.env['stock.warehouse'].search([('id','=',warehouse[0])]).lot_stock_id
        for line in self:
            line.qty_in = 0.0
            moves = self.env['stock.move'].search([('location_dest_id','=',loc_id.id),('product_id','=',line.id),('state','=','done')])
            for move in moves:
                line.qty_in += move.product_uom_qty

    show_cost_variation = fields.Boolean('Show Cost Variations', default=False)
    cost_table_id = fields.One2many('product.cost.table','product_id', 'Cost Variations')
    old_price = fields.Float('Old Price')
    #     compute='_compute_old_price', string="
    inventory_value = fields.Float(compute='_compute_inventory_value', string="Inventory Value")
    temp_remain = fields.Float('Qty')
    process_ok = fields.Boolean('Process')
    qty_in = fields.Float(compute='_compute_total_in_qty', string="Qty IN")
    allocation_no = fields.Char('Allocation No')




    @api.multi
    def show_cost_variation2(self):
        for line in self:
            line.show_cost_variation = True

    @api.multi
    def hide_cost_variation(self):
        for line in self:
            line.show_cost_variation = False


    @api.multi
    def unlink(self):
        for product in self:
            print 'self================================', product
        #             if invoice.state not in ('draft', 'cancel'):
        #                 raise Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
        #             elif invoice.internal_number:
        #                 raise Warning(_('You cannot delete an invoice after it has been validated (and received a number).  You can set it back to "Draft" state and modify its content, then re-confirm it.'))
        print 'aaaaaaaaaaaaaaaaaaaaaaaaaa'
        return super(product_template, self).unlink()



class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_num = 1

        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context)
            for line_rec in first_line_rec.order_id.order_line:
                line_rec.line_no = line_num
                line_num += 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    pro_old_price = fields.Float(related='product_id.standard_price', store=True, string='Previous Unit Price')
    task_id = fields.Many2one('project.task', 'Task')
    location_id = fields.Many2one(related='task_id.project_id.location_id', store=True, string='Location')

# class purchase_order(models.Model):
#     _inherit = 'purchase.order'
#
#
#
#


class stock_history(models.Model):
    _inherit = 'stock.history'



    uom_id = fields.Many2one(related='product_id.uom_id', string="Unit")
#     inventory_value_with_tax = fields.Float(compute='_compute_inventory_value_with_tax', store="True", string="Inventory Value With Tax")
#

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    @api.depends('project_ids')
    def _count_projects(self):

        for line in self:
            line.project_count = 0
            for lines in line.project_ids:
                line.project_count+=1


    tin_no = fields.Char('TIN NO', size=20)
    sp_code = fields.Char('Supplier Code', size=20)
    attachment_id = fields.One2many('ir.attachment', 'partner_id', 'Attachments')
    #     state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
    #                                    select=True, copy=False)
    guardian = fields.Char('guardian')
    kara = fields.Char('Kara')
    desam = fields.Char('Desam')
    village = fields.Char('Village')
    Municipality = fields.Char('Name of Municipality')
    taluk = fields.Char('Taluk')
    dist = fields.Char('District')
    age = fields.Integer('Age')
    post = fields.Char('Post')
    stage_id = fields.Many2one('project.stages', 'Customer Status')
    project_ids = fields.One2many('project.project', 'partner_id', 'Projects')
    project_count = fields.Integer(compute='_count_projects', store=True, string='No of Projects')
    contractor = fields.Boolean('Contractor')
    account_receivable = fields.Many2one(related='property_account_receivable', string='Account Receivable', store=True)
    account_payable = fields.Many2one(related='property_account_receivable', string='Account Payable', store=True)
#     power_of_attorny = fields.Text('Power of Attorny')

#     @api.multi
#     def action_sanction(self):
#         for line in self:
#             line.state = 'sanction'



class stock_picking(models.Model):
    _inherit="stock.picking"


    #     @api.onchange('move_lines')
    #     def change_dest_loation(self):
    #         print 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    #         if self.task_id.id != False:
    #             dest_location = self.task_id.project_id.location_id.id
    #             print 'qqqqqqqqqqqqqqqqqqqqqqqqqqqqqq', dest_location
    #
    # #             return {'value': {'move_lines': [(0, 0,  {'location_dest_id':dest_location})]}}
    # #             return {'value': {'location_dest_id': dest_location}}
    #             self.move_lines.update({'location_dest_id': dest_location})

    @api.multi
    @api.depends('move_lines')
    def _compute_is_stock_receipts(self):
        cr = self._cr
        uid = self._uid
        context = self._context
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        warehouse = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', user.company_id.id)], limit=1, context=context)
        loc_id = self.env['stock.warehouse'].search([('id','=',warehouse[0])]).lot_stock_id
        #         print 'loc_id===========================', loc_id
        for line in self:
            is_stock_reciept = False
            for move in line.move_lines:
                is_stock_reciept = False
                if move.location_dest_id.id == loc_id.id:
                    is_stock_reciept = True
            line.is_stock_reciept = is_stock_reciept



    @api.multi
    @api.depends('move_lines')
    def _compute_inventory_value(self):

        for line in self:
            for lines in line.move_lines:
                line.inventory_value+=lines.inventory_value

    def _state_get(self, cr, uid, ids, field_name, arg, context=None):
        '''The state of a picking depends on the state of its related stock.move
            draft: the picking has no line or any one of the lines is draft
            done, draft, cancel: all lines are done / draft / cancel
            confirmed, waiting, assigned, partially_available depends on move_type (all at once or partial)
        '''
        res = {}
        for pick in self.browse(cr, uid, ids, context=context):
            if (not pick.move_lines) or any([x.state == 'draft' for x in pick.move_lines]):
                res[pick.id] = 'draft'
                continue
            if all([x.state == 'cancel' for x in pick.move_lines]):
                res[pick.id] = 'cancel'
                continue
            if all([x.state in ('cancel', 'done') for x in pick.move_lines]):
                res[pick.id] = 'done'
                continue

            order = {'confirmed': 0, 'waiting': 1, 'assigned': 2}
            order_inv = {0: 'confirmed', 1: 'waiting', 2: 'assigned'}
            lst = [order[x.state] for x in pick.move_lines if x.state not in ('cancel', 'done')]
            if pick.move_type == 'one':
                res[pick.id] = order_inv[min(lst)]
            else:
                #we are in the case of partial delivery, so if all move are assigned, picking
                #should be assign too, else if one of the move is assigned, or partially available, picking should be
                #in partially available state, otherwise, picking is in waiting or confirmed state
                res[pick.id] = order_inv[max(lst)]
                if not all(x == 2 for x in lst):
                    if any(x == 2 for x in lst):
                        res[pick.id] = 'partially_available'
                    else:
                        #if all moves aren't assigned, check if we have one product partially available
                        for move in pick.move_lines:
                            if move.partially_available:
                                res[pick.id] = 'partially_available'
                                break
        #      print "res=========================================================================", res, ids
        if 'assigned' in res.values():
            #         print "res=========================================================================", res, ids
            res[ids[0]] = 'approve'
        return res

    def _get_pickings(self, cr, uid, ids, context=None):
        res = set()
        for move in self.browse(cr, uid, ids, context=context):
            if move.picking_id:
                res.add(move.picking_id.id)
        return list(res)
    #
    #     @api.multi
    #     @api.depends('change_help')
    #     def _compute_allow_request(self):
    #
    #         for line in self:
    #             print 'aaaaaaaaaaaaaaaaaaaaaaaaa'
    #             for lines in line.move_lines:
    #                 if lines.allow_to_request == False:
    #                     line.allow_to_request = False


    task_id = fields.Many2one('project.task', string="Related task")
    is_task_related = fields.Boolean('Related to task')
    is_other_move = fields.Boolean('Other Move')
    is_eng_request = fields.Boolean('Engineer Request')
    is_stock_reciept = fields.Boolean(compute='_compute_is_stock_receipts', store=True, string='Stock Receipt', default=False)
    inventory_value = fields.Float(compute='_compute_inventory_value', string='Inventory Value')
    changed_to_allocation = fields.Boolean('Changed To Allocation', default=False)
    request_user = fields.Many2one('res.users', 'Requested By')
    #     allow_to_request = fields.Boolean(compute='_compute_allow_request' , store=True, string='Allow To Request', default=True)
    #     change_help = fields.Boolean('Change', default=False)
    _columns = {
        'state': old_fields.function(_state_get, type="selection", copy=False,
                                     store={
                                         'stock.picking': (lambda self, cr, uid, ids, ctx: ids, ['move_type'], 20),
                                         'stock.move': (_get_pickings, ['state', 'picking_id', 'partially_available'], 20)},
                                     selection=[
                                         ('draft', 'Draft'),
                                         ('cancel', 'Cancelled'),
                                         ('waiting', 'Waiting Another Operation'),
                                         ('confirmed', 'Waiting Availability'),
                                         ('partially_available', 'Partially Available'),
                                         ('approve', 'Waiting for approval'),
                                         ('assigned', 'Ready to Transfer'),
                                         ('done', 'Transferred'),
                                     ], string='Status', readonly=True, select=True, track_visibility='onchange',
                                     help="""
                * Draft: not confirmed yet and will not be scheduled until confirmed\n
                * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
                * Waiting Availability: still waiting for the availability of products\n
                * Partially Available: some products are available and reserved\n
                * Ready to Transfer: products reserved, simply waiting for confirmation.\n
                * Transferred: has been processed, can't be modified or cancelled anymore\n
                * Cancelled: has been cancelled, can't be confirmed anymore"""
                                     ),
    }

    _defaults = {
        'request_user': lambda self, cr, uid, ctx=None: uid,
    }

    @api.multi
    def approve_picking(self):
        #         print "approve_picking==============================================="
        sql = ('UPDATE stock_picking '
               'SET state={} '
               'WHERE id={}').format('\'assigned\'', self[0].id)
        self.env.cr.execute(sql)

    @api.multi
    def set_to_draft(self):
        #         print "set to draft==============================================="
        sql = ('UPDATE stock_picking '
               'SET state={} '
               'WHERE id={}').format('\'draft\'', self[0].id)
        self.env.cr.execute(sql)

        sql = ('UPDATE stock_move '
               'SET state={} '
               'WHERE picking_id={}').format('\'draft\'', self[0].id)
        self.env.cr.execute(sql)

    def action_confirm(self, cr, uid, ids, context=None):
        todo = []
        todo_force_assign = []
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.location_id.usage in ('supplier', 'inventory', 'production'):
                todo_force_assign.append(picking.id)
            for r in picking.move_lines:
                if r.state == 'draft':
                    todo.append(r.id)
            if picking.is_eng_request == True:
                picking.changed_to_allocation = True
        if len(todo):
            self.pool.get('stock.move').action_confirm(cr, uid, todo, context=context)

        if todo_force_assign:
            self.force_assign(cr, uid, todo_force_assign, context=context)

        #         print 'test========================1',self,ids[0],self.browse(cr, uid, ids[0], context=context).move_lines
        allow = True
        for line in self.browse(cr, uid, ids[0], context=context).move_lines:
            if line.allow_to_request == False:
                allow = False
        if allow == False:
            raise osv.except_osv(_('Warning!'),
                                 _('You cannot request until the extra demand for products are approved.'))
        #             return {
        #                 'warning': {
        #                     'title': 'Warning',
        #                     'message': "You cannot request until the extra demand for products are approved"
        #                 }
        #             }

        return True

    #     from lxml import etree
    #     @api.model
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
        #         if view_type != 'form' and uid != SUPERUSER_ID:
        #             # Check if user is in group that allow creation
        #             has_my_group = self.env.user.has_group('group_warehouse_user')
        #             if not has_my_group:
        #                 root = etree.fromstring(res['arch'])
        #                 root.set('create', 'false')
        #                 res['arch'] = etree.tostring(root)
        return res
    #     @api.model
    #     def create(self,vals):
    #         print 'q---------------------------------------',vals.get('is_eng_request')
    #         context = self._context or {}
    #         if vals.get('is_eng_request') != True:
    #             print 'awearar============================',asfasfd
    #             if ('name' not in vals) or (vals.get('name') in ('/', False)):
    #                 ptype_id = vals.get('picking_type_id', context.get('default_picking_type_id', False))
    #                 sequence_id = self.pool.get('stock.picking.type').browse(self._cr, self._uid, ptype_id, context=context).sequence_id.id
    #                 vals['name'] = self.pool.get('ir.sequence').get_id(self._cr, self._uid,sequence_id, 'id', context=context)
    #         return super(stock_picking, self).create(vals)


    @api.multi
    def open_purchase_order(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['purchase.order'].search([('name','=',self.origin)])

        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Purchase Order view',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'purchase.order',
            'view_id':'purchase_order_form_changed',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }


class stock_move(models.Model):
    _inherit="stock.move"
    extra_quantity = 0

    @api.onchange('project_id','task_id')
    def _onchange_project(self):
        product_ids = []
        task_ids = []
        domain = {}
        if self.project_id and not self.task_id:
            for estimation in self.env['project.task.estimation'].search([('project_id','=',self.project_id.id)]):
                if estimation.pro_id.id not in product_ids:
                    product_ids.append(estimation.pro_id.id)
            domain['product_id'] = [('id','in',product_ids)]

        if self.project_id.id:
            self.location_dest_id = self.project_id.location_id
            task_ids = [task.id for task in self.env['project.task'].search([('project_id','=',self.project_id.id)])]
            domain['task_id'] = [('id','in',task_ids)]
        return {
            'domain': domain
        }

    @api.onchange('task_id')
    def _onchange_product_selection(self):
        #         result = super(stock_move, self).onchange_product_id(self.product_id.id,self.location_id,self.location_dest_id, False)
        #         if self.product_id.id:
        #             result = result['value']
        #             self.name = result['name']
        #             self.product_uom = result['product_uom']
        #             self.product_uos_qty = result['product_uos_qty']
        #             self.product_uom_qty = result['product_uom_qty']
        #             self.location_dest_id = result.get('location_dest_id', False)
        #             self.product_uos = result['product_uos']
        #             self.location_id = result.get('location_id', False)
        if self.task_id.id != False:
            product_ids = [estimate.pro_id.id for estimate in self.task_id.estimate_ids]

            self.location_dest_id = self.task_id.project_id.location_id

            return {
                'domain': {
                    'product_id': [('id','in',product_ids)]
                },
                #                 'value': {
                #                     'location_dest_id': self.task_id.project_id.location_id.id
                #                 }
            }


    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):
        #         print 'qqqqqqqqqqq98798798798090000000000000000000'
        super(stock_move, self).onchange_quantity(self.product_id.id, self.product_uom_qty, self.product_uom, self.product_uos)
        estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]
        #         print 'estimate===================', self.task_id.estimate_ids
        if not len(estimate):
            return
        if (estimate[0].qty - self.product_uom_qty)<0:
            #             print 'estimate[0].qty===========================', estimate[0].qty,self.product_uom_qty
            stock_move.extra_quantity = (self.product_uom_qty-estimate[0].qty)
            #             print
            self.product_uom_qty = estimate[0].qty
            self.is_request_more_btn_visible = True

            #             if self.picking_id.change_help == True:
            #                 self.picking_id.change_help = False
            #             if self.picking_id.change_help == False:
            #                 self.picking_id.change_help = True
            return {
                'warning': {
                    'title': 'Warning',
                    'message': "Quantity cannot be greater than the quantity assigned for the task. Please increase the quantity from the task."
                }
            }

    @api.multi
    @api.depends('product_id','product_uom_qty','price_unit')
    def _compute_inventory_value(self):

        for line in self:
            line.inventory_value = line.price_unit * line.product_uom_qty

    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_num = 1

        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context)
            for line_rec in first_line_rec.picking_id.move_lines:
                line_rec.line_no = line_num
                line_num += 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    is_request_more_btn_visible = fields.Boolean(default=False)
    is_task_related = fields.Boolean(related='picking_id.is_task_related', string='Related to task')
    #     task_id = fields.Many2one(related='picking_id.task_id', string="Related task")
    task_id = fields.Many2one('project.task', string="Related Task")
    inventory_value = fields.Float(compute='_compute_inventory_value', string='Inventory Value')
    #     price_unit = fields.Float(related='product_id.standard_price', string="Unit Price")
    available_qty = fields.Float(related='product_id.qty_available', store=True, string='Available Qty')
    allow_to_request = fields.Boolean('Allow To Request', default=True)
    project_id = fields.Many2one('project.project', string="Related Project")



    #     date = fields.Date('Date', required=True, select=True, help="Move date: scheduled date until move is done, then date of actual move processing", states={'done': [('readonly', True)]})


    def unlink(self, cr, uid, ids, context=None):
        context = context or {}
        #         print 'eeeeeeeeeeeeeeeeeeeeee======='
        for move in self.browse(cr, uid, ids, context=context):
            if move.state not in ('draft', 'cancel'):
                print 'qqwqw'
        #                 raise osv.except_osv(_('User Error!'), _('You can only delete draft moves.'))
        return super(stock_move, self).unlink(cr, uid, ids, context=context)


    def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False, loc_dest_id=False, partner_id=False):
        """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
        @param prod_id: Changed Product id
        @param loc_id: Source location id
        @param loc_dest_id: Destination location id
        @param partner_id: Address id of partner
        @return: Dictionary of values
        """
        if not prod_id:
            return {}
        user = self.pool.get('res.users').browse(cr, uid, uid)
        lang = user and user.lang or False
        if partner_id:
            addr_rec = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if addr_rec:
                lang = addr_rec and addr_rec.lang or False
        ctx = {'lang': lang}

        product = self.pool.get('product.product').browse(cr, uid, [prod_id], context=ctx)[0]
        uos_id = product.uos_id and product.uos_id.id or False
        result = {
            'name': product.partner_ref,
            'product_uom': product.uom_id.id,
            'price_unit': product.standard_price,
            'product_uos': uos_id,
            'product_uom_qty': 1.00,
            'product_uos_qty': self.pool.get('stock.move').onchange_quantity(cr, uid, ids, prod_id, 1.00, product.uom_id.id, uos_id)['value']['product_uos_qty'],
        }
        if loc_id:
            result['location_id'] = loc_id
        if loc_dest_id:
            result['location_dest_id'] = loc_dest_id
        return {'value': result}



    @api.multi
    def generate_prchase_order(self):
        self.ensure_one()
        view_id = self.env.ref('hiworth_construction.purchase_order_form_changed').id
        #         print 'qqqqqqqqqqqqqqqqqqqqqqqqq', view_id,self.picking_id.min_date
        context = self._context.copy()

        order_obj = self.env['purchase.order']
        order_line_obj = self.env['purchase.order.line']
        price_list = self.env['product.pricelist'].search([('name','=','Default Purchase Pricelist')])

        order_values = {'origin': self.picking_id.name,
                        'date_order': self.date,
                        'location_id': self.location_id.id,
                        'state': 'draft',
                        'minimum_planned_date': self.picking_id.min_date,
                        'pricelist_id': price_list.id,
                        #                         'related_usage': False,
                        }
        print 'order_obj============================', order_obj,order_line_obj
        order_id = order_obj.create(order_values)
        order_line_values = {'product_id': self.product_id.id,
                             'name': self.product_id.name,
                             'price_unit': self.product_id.standard_price,
                             'product_qty': self.product_uom_qty,
                             'date_planned': self.picking_id.min_date,
                             'order_id': order_id.id }
        line_id = order_line_obj.create(order_line_values)

        context = {'related_usage': False,
                   }
        return {
            'name':'Purchase Requisition',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id, 'form')],
            'res_model':'purchase.order',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':order_id.id,
            #             'target':'new',
            'context':context,
        }

    @api.multi
    def request_more_task_qty(self):
        return {
            'type': 'ir.actions.act_window',
            'id': 'test_id_act',
            'res_model': 'estimate.quantity.extra.request',
            'views': [[self.env.ref("hiworth_construction.estimate_quantity_extra_request_popup").id, "form"]],
            'target': 'new',
            'name': 'Send extra request',
            'context': {
                'default_task_id': self.picking_id.task_id.id,
                'default_product_id': self.product_id.id,
                'default_materialrequest_id': self.picking_id.id,
                'default_quantity': stock_move.extra_quantity,
                'default_date': fields.Datetime.now(),
                'default_move_id': self.id
            }
        }

class EstimateQuantityExtraRequest(models.Model):
    _name='estimate.quantity.extra.request'

    task_id = fields.Many2one('project.task', 'Task')
    product_id = fields.Many2one('product.product', 'Product')
    materialrequest_id  = fields.Many2one('stock.picking')
    quantity = fields.Float(string="Quantity")
    date = fields.Date()
    move_id = fields.Many2one('stock.move', 'Stock Move')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
    ],default='draft')

    @api.multi
    def extra_request_approve(self):
        self.ensure_one()
        estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]
        estimate[0].qty = estimate[0].qty+self.quantity
        self.state = 'approved'
        self.move_id.allow_to_request = True

    @api.multi
    def extra_request_reject(self):
        self.ensure_one()
        self.state = 'rejected'

    @api.multi
    def write(self,vals):
        if self.move_id.id != False:
            #             print 'aaaaaaaaaaaaaaaaaaa', self.move_id
            self.move_id.is_request_more_btn_visible = False
            self.move_id.allow_to_request = False
        #             if self.move_id.picking_id.change_help == True:
        #                 self.move_id.picking_id.change_help = False
        #             if self.move_id.picking_id.change_help == False:
        #                 self.move_id.picking_id.change_help = True
        super(EstimateQuantityExtraRequest, self).write(vals)
        return True


class res_groups(models.Model):
    _inherit = 'res.groups'

    company_group = fields.Boolean('Company Group')
