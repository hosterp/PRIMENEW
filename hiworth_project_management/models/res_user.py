# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
from openerp.osv import osv, fields
from openerp.tools.translate import _
import logging
from openerp import api

_logger = logging.getLogger(__name__)

class res_users(osv.Model):
    _inherit = 'res.users'

    _columns = {
        'mobile_password': fields.char(string='Mobile Password')
    }

    def create(self, cr, uid, vals, context=None):
        user_id = super(res_users, self).create(cr, uid, vals, context=context)
        user = self.browse(cr, uid, user_id, context=context)
        if user.partner_id.company_id: 
            user.partner_id.write({'company_id': user.company_id.id})
        if user.partner_id.email == False: 
            user.partner_id.write({'email': user.login})
        return user_id

    def signup(self, cr, uid, values, token=None, context=None):
        rec = 0
        if values.get('country'):
            country = values.get('country')
            rec = self.pool('res.country').search(cr,uid,[('name','=',country)])
            if len(rec) != 0:
                rec = rec[0]
            else:
                rec = self.pool('res.country').create(cr,uid,{'name':country,'code':'c'})
        rec_state = 0
        if values.get('state_new'):
            state = values.get('state_new')
            rec_state = self.pool('res.country.state').search(cr,uid,[('name','=',state)])
            if len(rec_state) != 0:
                rec_state = rec_state[0]
            else:
                rec_state = self.pool('res.country.state').create(cr,uid,{'name':state,'country_id':rec,'code':'s'})

            rec_state2 = self.pool('res.country.state').search(cr,uid,[('id','=',rec_state)])

           
        if context is None:
            context={}
        if token:
            res_partner = self.pool.get('res.partner')
            partner = res_partner._signup_retrieve_partner(
                        cr, uid, token, check_validity=True, raise_exception=True, context=None)
            partner_user = partner.user_ids and partner.user_ids[0] or False
            if not partner_user:
                print 'aaaaaaaaaaaa'
                values['street'] = values.get('street')
                values['street2'] = values.get('postoffice')
                values['city'] = values.get('city')
                values['zip'] = values.get('zips')
                values['phone'] = values.get('phone')
                values['mobile'] = values.get('mobile')
                # values['country_id'] = rec
                # values['state'] = values.get('state')
        else: 
            values['street'] = values.get('street')
            values['street2'] = values.get('postoffice')
            values['city'] = values.get('city')
            values['zip'] = values.get('zips')
            values['country_id'] = rec
            values['state_id'] = rec_state
            values['phone'] = values.get('phone')
            values['mobile'] = values.get('mobile')
            values['nick_name'] = values.get('nick_name')
            values['dob'] = values.get('dob')
            values['customer'] = True
            values['external_user'] = True
            _logger.info('WEBKUL OVERRIDEN METOD____%r',values)
        return super(res_users, self).signup(cr, uid, values, token, context=context)

class res_groups(osv.osv):
    _name = "res.groups"
    _inherit = 'res.groups'
    _columns = {
        'sequence': fields.integer(string='Sequence')
    }

class change_password_user(osv.TransientModel):
    """
        A model to configure users in the change password wizard
    """
    _inherit = 'change.password.user'

    def change_password_button(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            line.user_id.write({'password': line.new_passwd, 'mobile_password': line.new_passwd})
        self.write(cr, uid, ids, {'new_passwd': False}, context=context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
