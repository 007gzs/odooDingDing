import json
import logging
import time
from odoo import http, _
from odoo.addons.web.controllers.main import Home
from odoo.exceptions import UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class CallBack(Home, http.Controller):

    # 通讯录用户增加
    @http.route('/callback/user_add_org', type='json', auth='public')
    def callback_user_add_org(self, **kw):
        logging.info(">>>钉钉回调-用户增加事件")
        json_str = request.jsonrequest
        call_back, din_corpId = self.get_bash_attr()
        # ----------result-------------------------------
        signature = request.httprequest.args['signature']
        logging.info(">>>signature: {}".format(signature))
        timestamp = request.httprequest.args['timestamp']
        logging.info(">>>timestamp: {}".format(timestamp))
        nonce = request.httprequest.args['nonce']
        logging.info(">>>nonce: {}".format(nonce))
        # ----------result-end---------------------------
        msg = self.encrypt_result(json_str.get('encrypt'), call_back[0].aes_key, din_corpId)
        logging.info("-------------------------------------------")
        logging.info(">>>解密后的消息结果:{}".format(msg))
        logging.info("-------------------------------------------")
        msg = json.loads(msg)
        if msg.get('EventType') == 'user_add_org':
            logging.info("-------------------------------------------")
            logging.info(">>>钉钉回调-用户增加事件")
            logging.info("-------------------------------------------")
        # 返回加密结果
        return self.result_success(call_back[0].aes_key, call_back[0].token, din_corpId)

    # 通讯录用户变更事件
    @http.route('/callback/user_modify_org', type='json', auth='public')
    def callback_user_add_org(self, **kw):
        logging.info(">>>钉钉回调-通讯录用户变更事件")
        json_str = request.jsonrequest
        call_back, din_corpId = self.get_bash_attr()
        # 返回加密结果
        return self.result_success(call_back[0].aes_key, call_back[0].token, din_corpId)

    # 通讯录用户离职事件
    @http.route('/callback/user_leave_org', type='json', auth='public')
    def callback_user_add_org(self, **kw):
        logging.info(">>>钉钉回调-通讯录用户离职事件")
        json_str = request.jsonrequest
        call_back, din_corpId = self.get_bash_attr()
        # 返回加密结果
        return self.result_success(call_back[0].aes_key, call_back[0].token, din_corpId)

    def result_success(self, encode_aes_key, token, din_corpid):
        """
        封装success返回值
        :param encode_aes_key:
        :param token:
        :param din_corpid:
        :return:
        """
        from .dingtalk.crypto import DingTalkCrypto as dtc
        dc = dtc(encode_aes_key, din_corpid)
        # 加密数据
        encrypt = dc.encrypt('success')
        timestamp = str(int(round(time.time())))
        nonce = dc.generateRandomKey(8)
        # 生成签名
        signature = dc.generateSignature(nonce, timestamp, token, encrypt)
        new_data = {
            'json': True,
            'data': {
                'msg_signature': signature,
                'timeStamp': timestamp,
                'nonce': nonce,
                'encrypt': encrypt
            }
        }
        return new_data

    def encrypt_result(self, encrypt, encode_aes_key, din_corpid):
        """
        解密钉钉回调返回的值
        :param encrypt:
        :param encode_aes_key:
        :param din_corpid:
        :return: json-string
        """
        from .dingtalk.crypto import DingTalkCrypto as dtc
        dc = dtc(encode_aes_key, din_corpid)
        return dc.decrypt(encrypt)

    def get_bash_attr(self):
        call_back_list = request.env['dindin.users.callback.list'].sudo().search([('value', '=', 'user_add_org')])
        call_back = request.env['dindin.users.callback'].sudo().search([('call_id', '=', call_back_list[0].id)])
        if not call_back:
            raise UserError("钉钉回调管理单据错误，无法获取token和encode_aes_key值!")
        din_corpId = request.env['ir.config_parameter'].sudo().get_param('ali_dindin.din_corpId')
        if not din_corpId:
            raise UserError("钉钉CorpId值为空，请前往设置中进行配置!")
        return call_back, din_corpId
