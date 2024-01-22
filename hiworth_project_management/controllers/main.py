import openerp
import openerp.http as http
from openerp.http import request
from passlib.context import CryptContext


class PopupController(openerp.http.Controller):

    @http.route('/hiworth_project_management/notify_msg', type='json', auth="none")
    def notify_msg(self):
        user_id = request.session.get('uid')
        return request.env['popup.notifications'].sudo().search(
            [('name', '=', user_id), ('status', '!=', 'shown')]
        ).get_notifications()

    @http.route('/get_encryption', type='json', auth="public")
    def get_encryption(self, password):

        password_crypted = CryptContext(['pbkdf2_sha512', 'md5_crypt'], deprecated=['md5_crypt']).encrypt(password)

        a = {"encrypted": password_crypted}

        return a

    @http.route('/hiworth_project_management/notify_msg_ack', type='json', auth="none")
    def notify_msg_ack(self, notif_id, type='json'):
        notif_obj = request.env['popup.notifications'].sudo().browse([notif_id])
        if notif_obj:
            notif_obj.status = 'shown'
            if notif_obj.message_bool == True:
                if notif_obj.message_id:
                    notif_obj.message_id.seen = True
           
            notif_obj.unlink()

 