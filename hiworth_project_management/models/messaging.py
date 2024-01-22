from openerp import models, fields, api, _
import uuid
import sys, zipfile, xml.dom.minidom
import pytz

class ImChatMessage(models.Model):
    _name = 'im_chat.message.req'
    _order = 'id desc'

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            if record.from_id and record.message_type:
                result.append((record.id,u"%s (%s)" % (record.from_id.name, (record.message_type).capitalize())))
        return result

    @api.onchange('to_id')
    def onchange_to_id(self):
        ids = []

        users = self.env['res.users'].sudo().search([])
        for user_id in users:
            if self.message_type == 'official':
                if user_id.partner_id.customer != True:
                    ids.append(user_id.id)
            else:

                ids.append(user_id.id)

        return {'domain': {'to_id': [('id', 'in', ids)]}}

    from_id = fields.Many2one('res.users','From',readonly=True)
    nick_name = fields.Char('Nick Name',related='from_id.partner_id.nick_name',readonly=True)
    req_gen = fields.Boolean('REQGEN',default=False)
    no_edit = fields.Boolean(default=False)
    to_id = fields.Many2one('res.users','To')
    cc_ids = fields.Many2many('res.users','message_cc_rel','message_id','user_id',string='Cc')
    cc_id = fields.Many2one('res.users','Ccs')
    message = fields.Text('Leave a Message Here..',required=True)
    user_id = fields.Many2one('res.users', 'User')
    pending_task_reply = fields.Selection([('draft','Draft'),('shown','Shown')],default='draft')
    state = fields.Selection([('new','New'),
            ('draft','Draft'),
            ('pending','Pending'),
            ('approved','Approved'),
        ], string='Status', readonly=True, default='approved',
         copy=False)
    bool_msg = fields.Boolean(default=False)
    require = fields.Boolean(default=True)
    reply = fields.Text('Reply')
    date_today = fields.Datetime('Date',default=fields.Datetime.now)
    convert_task = fields.Boolean(default=False)
    related_project = fields.Many2one('project.project','Related Project')
    admin = fields.Many2one('res.users', 'Admin')
    message_type = fields.Selection([('general','General'),('requirement','Requirement'),('official','Official')],string="Messaging Type")
    message_type2 = fields.Selection([('general','General'),('requirement','Requirement')],string="Messaging Type")
    status = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
    status1 = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')
    add_member = fields.One2many('assigned.member','as_id')
    attachment_idss = fields.One2many('ir.attachment','att_ids')
    has_attachment = fields.Boolean('Has Attachment',default=False)
    sent = fields.Boolean(default=False)
    delete_msg = fields.Boolean(default=False)
    done_mem = fields.Boolean(default=False)
    cc_bool = fields.Boolean(default=False)
    approved_user = fields.Many2one('res.users')
    to_admin_req = fields.Boolean(default=False)
    forward_by = fields.Many2one('res.users','Forwarded By',readonly=True)
    fwd_msg = fields.Boolean(default=False)
    customer = fields.Many2one('res.users','customer',readonly=True)
    req_nofify = fields.Selection([('draft','Draft'),('shown','Shown')],default='draft')
    req_id = fields.Many2one('im_chat.message.req')
    seen = fields.Boolean('Seen')

    @api.multi
    def delete_msg_inbox(self):
        self.delete_msg = True
        return {
                'name': 'Inbox',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'im_chat.message.req',
                'domain': [('to_id','=',self.to_id.id),('require','=',True),('delete_msg','=',False),('state','=','approved')],

                'target': 'current',
                'type': 'ir.actions.act_window',
                'context': {},

            }

    @api.multi
    def back_to_inbox(self):
        self.delete_msg = False
        return {
                'name': 'Deleted Messages',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'im_chat.message.req',
                'domain': [('to_id','=',self.to_id.id),('delete_msg','=',True)],

                'target': 'current',
                'type': 'ir.actions.act_window',
                'context': {},

            }



    _defaults = {
        'from_id':lambda obj, cr, uid, ctx=None: uid,
        'user_id': lambda obj, cr, uid, ctx=None: uid,
        'admin': lambda obj, cr, uid, ctx=None: 1,
        }

    @api.onchange('attachment_idss')
    def onchange_attachment_ids(self):
        if self.attachment_idss:
            self.has_attachment = True
        else:
            self.has_attachment = False

    @api.onchange('message_type')
    def onchange_req_gen(self):
        if self.message_type == 'general' or self.message_type == 'official':
            self.req_gen = True
        else:
            self.req_gen = False


    @api.multi
    def general_message(self):
        self.state = 'new'

    @api.model
    def create(self, vals):
        if vals.get('message_type2'):
            vals['message_type'] = vals.get('message_type2')
        result = super(ImChatMessage, self).create(vals)
        if result.state == 'approved':
            create_popup_main = self.env['popup.notifications'].sudo().create(
                                                                        {
                                                                        'message_bool':True,
                                                                        'name':result.to_id.id,
                                                                        'status':'draft',
                                                                        'message':"You have a "+str(result.message_type)+ " message \n"+str(result.message)+ "\n from "+str(result.from_id.name),
                                                                        'message_id':result.id
                                                                        })
        if result.to_admin_req == True:
            result.req_gen = False
        rec_attc = []
        if result.attachment_idss:
            for att in result.attachment_idss:
                rec_attc.append((0,0,{'name':att.name,'datas':att.datas}))
        
           
        result.cc_id = result.to_id.id

        if result.no_edit == False:
            result.no_edit = True
        # res_id = [result]
        to_users = []
        if (result.from_id.customer == True and result.message_type == 'requirement') or result.state == 'pending':
            print 'test========================0'
            group_id_admin1 = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_admin1').id
            group_id_admin2 = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_admin2').id
            group_id_general_manager = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_general_manager').id
            group_id_dgm = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_dgm').id
            group_id_manager_office = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_manager_office').id
            group_id_am_office = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_am_office').id
            group_id_archiect = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_architect').id
            group_id_employee = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_employee').id

            # print 'group_id_admin1===============================', group_id_admin1
            to_type = 8
            to_id = result.to_id.id
            print 'to_id================1', to_id
            if result.state == 'pending':
                to_id = result.from_id.id
            print 'to_id================1', to_id
            self._cr.execute("select uid from res_groups_users_rel where gid=%s and uid =%s", (group_id_employee,to_id,))
            if len(self._cr.fetchall()) > 0:
                to_type = 1
            self._cr.execute("select uid from res_groups_users_rel where gid=%s and uid =%s", (group_id_archiect,to_id,))
            if len(self._cr.fetchall()) > 0:
                to_type = 2
            # if result.state == 'pending':
            self._cr.execute("select uid from res_groups_users_rel where gid=%s and uid =%s", (group_id_am_office,to_id,))
            if len(self._cr.fetchall()) > 0:
                to_type = 3
            self._cr.execute("select uid from res_groups_users_rel where gid=%s and uid =%s", (group_id_manager_office,to_id,))
            if len(self._cr.fetchall()) > 0:
                to_type = 4
            self._cr.execute("select uid from res_groups_users_rel where gid=%s and uid =%s", (group_id_dgm,to_id,))
            if len(self._cr.fetchall()) > 0:
                to_type = 5
            self._cr.execute("select uid from res_groups_users_rel where gid=%s and uid =%s", (group_id_general_manager,to_id,))
            if len(self._cr.fetchall()) > 0:
                to_type = 6
            self._cr.execute("select uid from res_groups_users_rel where gid=%s and uid =%s", (group_id_admin2,to_id,))
            if len(self._cr.fetchall()) > 0:
                to_type = 7
            self._cr.execute("select uid from res_groups_users_rel where gid=%s and uid =%s", (group_id_admin1,to_id,))
            if len(self._cr.fetchall()) > 0:
                to_type = 8
            print 'to_type===================', to_type
            # to_users = []
            if to_type < 8:
            # dgm_list = []
                group_id_admin1 = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_admin1').id
                group_admin1 = self.env['res.groups'].search([('id','=',group_id_admin1)])
                for user in group_admin1.users:
                    if user.id not in to_users and user.id != result.to_id.id:
                        to_users.append(user.id)
                    # if user.id not in dgm_list  and user.id != result.to_id.id:
                    #     dgm_list.append(user.id)

            if to_type < 7:
                group_id_admin2 = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_admin2').id
                group_admin2 = self.env['res.groups'].search([('id','=',group_id_admin2)])
                for user in group_admin2.users:
                    if user.id not in to_users and user.id != result.to_id.id:
                        to_users.append(user.id)
                # if user.id not in dgm_list and user.id != result.to_id.id:
                #     dgm_list.append(user.id)

            if to_type < 6:
                group_id_general_manager = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_general_manager').id
                group_general_manager = self.env['res.groups'].search([('id','=',group_id_general_manager)])
                for user in group_general_manager.users:
                    if user.id not in to_users and user.id != result.to_id.id:
                        to_users.append(user.id)
                    # if user.id not in dgm_list  and user.id != result.to_id.id:
                    #     dgm_list.append(user.id)
            
            if to_type < 5:
                group_id_dgm = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_dgm').id
                group_dgm = self.env['res.groups'].search([('id','=',group_id_dgm)])
                for user in group_dgm.users:
                    # if user.id not in dgm_list and user.id != result.to_id.id:
                    #     if result.related_project.company_id.id in [i.id for i in user.company_ids]:
                    #         dgm_list.append(user.id)
                    if result.related_project.company_id.id in [i.id for i in user.company_ids]:
                        if user.id not in to_users and user.id != result.to_id.id:
                            to_users.append(user.id)


            # if to_type < 4:
            #     group_id_manager_office = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_manager_office').id
            #     group_manager_office = self.env['res.groups'].search([('id','=',group_id_manager_office)])
            #     for user in group_manager_office.users:
            #         if user.id not in to_users:
            #             if user.company_id.id == result.related_project.company_id.id:
            #                 to_users.append(user.id)

            # if to_type < 3:
            #     group_id_am_office = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_am_office').id
            #     group_am_office = self.env['res.groups'].search([('id','=',group_id_am_office)])
            #     for user in group_am_office.users:
            #         if user.id not in to_users:
            #             if user.company_id.id == result.related_project.company_id.id:
            #                 to_users.append(user.id)

            if result.related_project.user_id.id not in to_users and result.state != 'pending':
                to_users.append(result.related_project.user_id.id)

            # check_employee = []
            # group_id_employee = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_employee').id
            # group_id_archiect = self.env['ir.model.data'].get_object('hiworth_project_management',  'group_architect').id
            # group_employee = self.env['res.groups'].search([('id','=',group_id_employee)])
            # group_architect = self.env['res.groups'].search([('id','=',group_id_archiect)])
            # for user in group_employee.users:
            #     if user.id not in check_employee:
            #         if user.company_id.id == result.related_project.company_id.id:
            #             check_employee.append(user.id)

            # for user in group_architect.users:
            #     if user.id not in check_employee:
            #         if user.company_id.id == result.related_project.company_id.id:
            #             check_employee.append(user.id)

            # flag_cc = 0
            cc_ids_list = [i.id for i in result.cc_ids] 
            # if result.to_id.id in check_employee:
            #     flag_cc = 1
            #     cc_ids_list1 = cc_ids_list + to_users
            if result.state != 'pending':
                print 'user==============', to_users
                if result.to_id.id in to_users: to_users.remove(result.to_id.id)
                print 'user==============2', to_users
                for user in to_users: 
                    values = {
                        'from_id' :result.from_id.id,
                        'to_id' :result.to_id.id,
                        'message_type':result.message_type,
                        'related_project':result.related_project.id,
                        'date_today':fields.Datetime.now(),
                        'message':result.message,
                        'cc_ids': [(6, 0, cc_ids_list)],
                        'attachment_idss':rec_attc,
                        'no_edit':True,
                        'sent':True,
                        'cc_id':user,
                        'req_id':result.id,
                        }
                    
                    create1 = super(ImChatMessage, self).create(values)
                    if result.state == 'approved':

                        create_popup = self.env['popup.notifications'].sudo().create(
                                                                        {
                                                                        'message_bool':True,
                                                                        'name':user,
                                                                        'status':'draft',
                                                                        'message':'You have a '+ str(result.message_type)+ " message \n"+str(result.message)+ "\n from "+str(result.from_id.name),
                                                                        'message_id':create1.id
                                                                        })

            print 'test=============', result.state,to_users
            if result.state == 'pending':
                for user in to_users: 
                    create_popup = self.env['popup.notifications'].sudo().create(
                                                                    {
                                                                    # 'message_bool':True,
                                                                    'name':user,
                                                                    'status':'draft',
                                                                    'message':'You have a '+ str(result.message_type)+ " message \n"+str(result.message)+ "\n from "+str(result.from_id.name) + " to approve.",
                                                                    # 'message_id':create1.id
                                                                    })

        if result.cc_ids:
            for ccs in result.cc_ids:
                # if flag_cc == 1:
                    if ccs.id not in to_users:
                        values_cc = {
                            'from_id' :result.from_id.id,
                            'require': True,
                            'to_id' :result.to_id.id,
                            'message_type':result.message_type,
                            'req_gen' :False if result.message_type == 'requirement' else True,
                            'cc_ids': [(6, 0, [i.id for i in result.cc_ids])],
                            'cc_id':ccs.id,
                            'related_project':result.related_project.id,
                            'date_today':fields.Datetime.now(),
                            'message':result.message,
                            'attachment_idss':rec_attc,
                            'no_edit':True,
                            'cc_bool':True,

                            }

                        
                        create_cc = super(ImChatMessage, self).create(values_cc)
                        if result.state == 'approved':

                            create_popup = self.env['popup.notifications'].sudo().create(
                                                                                {
                                                                                'message_bool':True,
                                                                                'name':ccs.id,
                                                                                'status':'draft',
                                                                                'message':"You have a "+str(result.message_type)+ " message \n"+str(result.message)+ "\n from "+str(result.from_id.name),
                                                                                'message_id':create_cc.id
                                                                                })
        # print asdasd
        return result


    # @api.multi
    # def write(self, vals):
    #     if vals.get('message_type2'):
    #         vals['message_type'] = vals.get('message_type2')
    #     result = super(ImChatMessage, self).create(vals)
    #     return result

    @api.multi
    def task_message(self):
        self.req_gen = True
        self.done_mem = False
        record = []
        rec = self.env['im_chat.message.req'].sudo().search([('req_id','=',self.req_id.id)])
        for val in self.add_member:
            if val.assigned_to.id not in record:
                values = {
                    'as_id': val.id,
                    'assigned_to': val.assigned_to.id,
                    }
                record.append((0, False, values ))


        for recs in rec:
            if recs.id != self.id:
                recs.add_member = record




    # @api.multi
    # def get_notifications(self):
    #     result = []
    #     for obj in self:
    #         result.append({
    #             'title': obj.message,
    #             'title1': obj.reply,
    #             'user':obj.from_id.name,
    #             'status': obj.status,
    #             'status1': obj.status1,
    #             'message_type':(obj.message_type).title(),
    #             'id': obj.id,
    #             'id1':obj.from_id.id,
    #             'req_nofify': obj.req_nofify,
    #             'pending_task_reply':obj.pending_task_reply,
    #             'approved_user':obj.approved_user.name
    #         })
    #     return result


    @api.onchange("related_project")
    def onchange_related_project_line(self):
        if self.from_id:
            ids = []
            if self.from_id.partner_id.customer == True:
                record = self.env['project.project'].search([('partner_id','=',self.from_id.partner_id.id)])

                if record:
                    for item in record:
                        ids.append(item.id)
                    return {'domain': {'related_project': [('id', 'in', ids)]}}
                else:
                    return {'domain': {'related_project': [('id', 'in', ids)]}}
            else:
                # record2 = self.env['project.user.rel'].search([('uid','=',self.from_id.id)])
                self.env.cr.execute('SELECT project_id from project_user_rel where uid= %s' % self.from_id.id)

                res = self.env.cr.fetchall()
                for r in res:
                    if r:
                        ids.append(r[0])
                return {'domain': {'related_project': [('id', 'in', ids)]}}

    @api.onchange("to_id","related_project","message_type","from_id")
    def onchange_to_id_line(self):
        ids = []
        if self.from_id.partner_id.customer == True and not self.env.user.id == 1:
            if self.related_project:
                record = self.env['project.project'].search([('partner_id','=',self.from_id.partner_id.id),('id','=',self.related_project.id)])
                if record:
                    if record.members:
                        for item in record.members:
                            ids.append(item.id)
                        return {'domain': {'to_id': [('id', 'in', ids)]}}
                    else:
                        return {'domain': {'to_id': [('id', 'in', ids)]}}
                else:
                    return {'domain': {'to_id': [('id', 'in', ids)]}}
            else:
                records = self.env['project.project'].search([('partner_id','=',self.from_id.partner_id.id)])
                for record in records:
                    if record.members:
                        for item in record.members:
                            ids.append(item.id)
                return {'domain': {'to_id': [('id', 'in', ids)]}}
        else:
            rec = self.env['res.users'].search([('partner_id.is_cus','!=',True),('id','!=',self.from_id.id)])
            # print 'rec===========================', rec
            for user in rec:
                ids.append(user.id)
            return {'domain': {'to_id': [('id', 'in', ids)]}}



    @api.onchange('to_id')
    def _onchange_to_id_cc(self):
        if self.to_id:
            list = []
            rec = self.env['res.users'].search([('id','!=',self.to_id.id)])
            for record in rec:
                list.append(record.id)
            return {'domain': {'cc_ids': [('id', 'in', list)]}}



    @api.multi
    def task_convert(self):
        view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_project_employee_charge_form')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('Employee InCharge'),
           'res_model': 'employee.charge',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'new',
           'context': {'default_rec':self.id}
       }

        return res

    @api.multi
    def approved_message(self):
        self.state = 'approved'
        self.approved_user = self.env.user.id
        self.require = True
        self.bool_msg = True
        self.done_mem = False
        self.status = 'draft'
        # rec = self.env['project.project'].search([('partner_id','=',self.to_id.partner_id.id),('id','=',self.related_project.id)])

    @api.multi
    def forward_msg(self):

        ids = self.to_id.id
        view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_project_message_requirement_form_forward')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('Forward'),
           'res_model': 'im_chat.message.req',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'current',
           'context': {'default_fwd_msg':True,'default_customer':self.from_id.id,'default_req_gen':False,'default_to_admin_req':True,'default_forward_by':self.env.user.id,'default_from_id':self.env.user.id,'default_status':'draft','default_status1':'draft','default_message_type':self.message_type,'default_related_project':self.related_project.id,'default_require':True,'default_message':self.message,'default_state':'approved','default_bool_msg':True,'default_req_gen':True}
       }

        return res

    @api.multi
    def reply_message(self):

        ids = self.customer.id if self.customer.id != False else self.from_id.id
        view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_project_message_requirement_form')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('Reply'),
           'res_model': 'im_chat.message.req',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'current',
           'context': {'default_cc_ids':[(6, 0, [i.id for i in self.cc_ids])] if self.message_type != 'requirement' else False,'default_done_mem':False,'default_status':'draft' if self.message_type != 'requirement' else 'shown','default_message_type':self.message_type,'default_related_project':self.related_project.id,'default_require':True if self.message_type != 'requirement' else False,'default_reply':self.message,'default_to_id':ids,'default_state':'pending' if self.message_type == 'requirement' else 'approved','default_bool_msg':True,'default_req_gen':True}
       }

        return res


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.onchange('datas','datas_fname')
    def onchange_datas(self):
        if self.datas or self.datas_fname:
            self.name = self.datas_fname

    @api.multi
    def set_image_gallery(self):
        if self.datas:
            record = []
            att_id = self.env['ir.attachment'].create({'datas':self.datas,'name':self.name})
            record.append(att_id.id)
            for att in self.gallery_img.site_images:
                record.append(att.id)
            self.gallery_img.write({'site_images' : [(6, 0, record)]})


    @api.multi
    def set_image(self):
        print "saved..."
        if self.datas:
            record = []
            att_id = self.env['ir.attachment'].create({'datas':self.datas,'name':self.name,'gallery':False})
            record.append(att_id.id)
            for att in self.project_image.site_image:
                record.append(att.id)
            self.project_image.write({'site_image' : [(6, 0, record)]})

    @api.multi
    def view_image(self):
        view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_ir_attachment_form_view_image')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('View Image'),
           'res_model': 'ir.attachment',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'new',
           'context': {'default_name':self.name,'default_datas':self.datas}
       }
     
        return res
        



    att_ids = fields.Many2one('im_chat.message.req', )
    project_image = fields.Many2one('project.project')
    gallery_img = fields.Many2one('gallery.project')
    gallery = fields.Boolean(default=False)
    drawing_id = fields.Many2one('project.project')


class TaskMessage(models.Model):
    _name = 'task.message'
    _order = 'id desc'

    rec = fields.Many2one('im_chat.message.req')
    from_id = fields.Many2one('res.users',string='From')
    to = fields.Many2one('res.users',string="To")
    message = fields.Char('Message')
    reply = fields.Char('Reply')
    manager = fields.Many2one('res.users','Manager')
    convert_task = fields.Boolean(default=False)
    project = fields.Many2one('project.project','Project',readonly=True)
    date = fields.Datetime('Date')
    assigned = fields.Many2one('res.users','Assigned To')
    admin = fields.Many2one('res.users', 'Admin')
    status = fields.Selection([('shown', 'shown'), ('draft', 'draft')], default='draft')

    _defaults = {
        'admin': lambda obj, cr, uid, ctx=None: 1,
        }

    @api.multi
    def get_notifications(self):
        result = []
        for obj in self:
            result.append({
                'title': obj.message,
                'user':obj.from_id.name,
                'logged':obj.to.name,
                'status': obj.status,
                'id': obj.id,
            })
        return result



    @api.multi
    def task_convert(self):
        view_ref = self.env['ir.model.data'].get_object_reference('hiworth_project_management', 'view_project_employee_charge_form')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('Employee InCharge'),
           'res_model': 'employee.charge',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'new',
           'context': {'default_recs':self.id,'default_employee':self.assigned.id}
       }

        return res

class TaskMessage(models.Model):
    _name = 'task.mes'

    rec = fields.Many2one('im_chat.message.req')
    from_id = fields.Many2one('res.users',string='From')
    to = fields.Many2one('res.users',string="To")
    message = fields.Char('Message')
    manager = fields.Many2one('res.users','Manager')
    convert_task = fields.Boolean(default=False)
    project = fields.Many2one('project.project','Project',readonly=True)
    date = fields.Datetime('Date')
    assigne = fields.Many2one('res.users','Assigned To')
    start_time = fields.Datetime('Starting Time')




    @api.model
    def create(self, vals):
        result = super(TaskMessage, self).create(vals)
        return result

    @api.multi
    def confirm_task(self):
        self.env['task.message'].create({
                                'from_id':self.to.id,
                                'to':self.from_id.id,
                                'message':self.message,
                                'date':self.date,
                                'assigned':self.assigned.id,
                                'project':self.project.id
            })
        self.rec.state = 'new'
        return



class AssigningMember(models.Model):
    _name = 'assigned.member'

    @api.onchange('assigned_to','as_id')
    def onchange_user_id_pro(self):
        ids = []
        ids = [user.id for user in self.env['res.users'].sudo().search([('partner_id.is_cus','!=',True)])]
        return {'domain': {'assigned_to': [('id', 'in', ids)]}}

    assigned_ids = fields.Many2one('task.mes')
    as_id = fields.Many2one('im_chat.message.req')
    assigned_to = fields.Many2one('res.users','Job Assigned To')

    @api.multi
    def add_member(self):
        self = self.sudo()
        return {
            'name': 'Task conversation_state',
            'view_type': 'form',
            'view_mode': 'calendar,tree,form',
            'res_model': 'event.event',
            'domain': [('user_id', '=', self.assigned_to.id)],
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {'default_user_id':self.assigned_to.id,'default_name':self.as_id.message,'default_project_id':self.as_id.related_project.id,'default_civil_contractor':self.as_id.related_project.partner_id.id,'default_project_manager':self.as_id.related_project.user_id.id}
        }

class EmployeeCharge(models.Model):
    _name = 'employee.charge'

    task_category = fields.Many2one('event.type','Task Category')
    employee = fields.Many2one('res.users','Assigned To')
    recs = fields.Many2one('task.message')

    @api.multi
    def confirm_employee(self):
        self.recs.convert_task = True
        uom = self.env['product.uom'].search([])
        rec = self.env['project.project'].search([('partner_id','=',self.recs.to.partner_id.id),('id','=',self.recs.project.id)])
        if rec:
            self.env['event.event'].sudo().create({'event_project':rec.id,'type':self.task_category.id,'date_begin':fields.Datetime.now(),'date_end':fields.Datetime.now(),'project_manager':rec.user_id.id,'name':self.recs.message,'project_id':rec.id,'civil_contractor':self.recs.to.id,'user_id':self.employee.id})

