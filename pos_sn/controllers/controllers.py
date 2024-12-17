#-*- coding: utf-8 -*-

from odoo import http
from odoo.http import request
from werkzeug.utils import redirect
import json
import logging

# Configuración del logger
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]"
)
_logger = logging.getLogger(__name__)

def log_message(message, do=False):

    if do:
        try:
            file_path = r'D:\SOFTNOW\ODOO\ADDONS\pos_sn\controllers\odoo_custom_log.txt'
            with open(file_path, 'a') as fx:
                fx.write(str(message)+'\n')
        except Exception as e:
            _logger.error(e)


class PtvSn(http.Controller):

    @http.route('/verify_order_line_done_status')
    def get_done_status(self, **kwargs):
        '''
        Obtiene el estado de una orderline
        '''
        if 'order_line_id' in request.params:
            order_line_id = int(request.params['order_line_id'])
            o_line = http.request.env['pos.order.line'].search([('id', '=', order_line_id)])
            data = {'status':bool(o_line.order_line_done), 'order_line_id':order_line_id}
        else:
            data = {'status':False, 'order_line_id':None}

        # Crear una respuesta JSON utilizando Response
        json_data = json.dumps(data)

        response = request.make_response(json_data, headers=[('Content-Type', 'application/json')])
        return response
    
    @http.route('/close_full_order')
    def close_full_order(self, *kwargs):
        '''
        Cierra la orden en la vista del cocinero
        '''
        if 'order_id' in request.params:
            o_id = int(request.params['order_id'])
            o_line = http.request.env['pos.order'].search([('id', '=', o_id)])
            o_line.update({'kitchen_done': True})

    @http.route('/downgrade_order_line')
    def downgrade_order_line(self, **kwargs):
        '''
        Actualiza estado de orden
        '''
        if 'line_order_id' in request.params:
            l_id = int(request.params['line_order_id'])
            data = {'OID':l_id}
            l_line = http.request.env['pos.order.line'].search([('id', '=', l_id)])
            l_line.update({'order_line_done': False})
        else:
            data = {'OID':False}

        # Convertir el diccionario en una cadena JSON
        json_data = json.dumps(data)

        # Crear una respuesta JSON utilizando Response
        response = request.make_response(json_data, headers=[('Content-Type', 'application/json')])

        return response
    
    @http.route('/upgrade_order_line')
    def upgrade_order_line(self, **kwargs):
        '''
        Actualiza estado de orden
        '''
        if 'line_order_id' in request.params:
            l_id = int(request.params['line_order_id'])
            data = {'OID':l_id}
            l_line = http.request.env['pos.order.line'].search([('id', '=', l_id )])
            l_line.update({'order_line_done': True})
        else:
            data = {'OID':False}

        # Convertir el diccionario en una cadena JSON
        json_data = json.dumps(data)

        # Crear una respuesta JSON utilizando Response
        response = request.make_response(json_data, headers=[('Content-Type', 'application/json')])

        return response

    @http.route('/comandas', website=True, auth='public')
    def comandas(self, **kw):
        
        #-- Obtener las sessiones activas
        sesiones = http.request.env['pos.session'].search([('state', '=', 'opened')])

        #-- Empaquetar los pedidos organizados por sesion y orden
        sessions = {}
        for s in sesiones:
            #-- Crea un diccionario para alojar los datos de la sesion actual
            sessions.update({s.name:{} })

            #-- Obtener las ordenes pendientes en esta sesion
            #ordenes = http.request.env['pos.order'].search([('state', '!=', 'done'), ('session_id', '=', s.id)])
            ordenes = http.request.env['pos.order'].search([('kitchen_done', '=', False), ('session_id', '=', s.id)])

            for o in ordenes:
                #-- Obtiene los pedidos asociados a la orden actual
                pedidos = http.request.env['report.pos.order'].search([('state', '=', 'draft'),
                                                                       ('session_id','=', s.id),
                                                                       ('order_id','=', o.id),
                                                                       ('state', '!=', 'done')])
                #-- Agrega los pedidos de la orden actual
                if o.table_id.active:
                    if pedidos:
                        sessions[s.name].update({o.table_id.name:pedidos})
       
        #-- Obtener los pedidos de pos_order_line
        #Con el id y order_id del pedido puedo buscar la nota del usuario en order_lines
        # o.id y o.order_id
        order_lines = http.request.env['pos.order.line'].search([('is_total_cost_computed', '=', None),
                                                                 ('order_line_done','!=', True)
                                                                ])

        # sessions = {'sesion1': {'orden1':[p1 ,p2, ...], 'orden2':[p1 ,p2, ...]}, 'sesion2':{}}
        return http.request.render('pos_sn.comandas_ptv', {'sessions':sessions, 'order_lines':order_lines})
    

class DynamicBaseUrl(http.Controller):

    @http.route(['/shop/table/<int:table_id>'], type='http', auth='public', website=True)
    def save_table_id(self, table_id=None, **kwargs):

        # -- Actualizar la URL base
        base_url = request.env['ir.config_parameter'].sudo().get_param('fixed_url')
        if base_url:
            request.env['ir.config_parameter'].sudo().set_param('web.base.url', base_url)

        # -- Crear una variable de sesion en el objeto request
        request.session['table_id'] = table_id

        #-- Captura de la variable en otro modelo
        #table_id = request.session.get('table_id')

        return redirect('/shop')
    
    @http.route(['/shopx'], type='http', auth='public', website=True)
    def shopx(self, **kwargs):
        base_url = request.env['ir.config_parameter'].sudo().get_param('fixed_url')
        if base_url:
            request.env['ir.config_parameter'].sudo().set_param('web.base.url', base_url)
        return redirect('/shop')


class UserController(http.Controller):

    @http.route('/order_search', type='http', auth='public', methods=['GET'], csrf=False)
    def order_search(self, **kw):
        return http.request.render('pos_sn.ptv_viewer_form')
    
    @http.route('/viewer', type='http', auth='public', methods=['GET'], csrf=False)
    def orders_viewer(self, **kw):

        order_name = kw.get('order_name', None)
        orders = []

        #-- Obtener las ordenes con estado de orden 'required' or 'preparing'
        sale_orders = http.request.env['sale.order'].sudo().search([('order_status', 'not in', ('ended',))])
        for s in sale_orders:
            if s.state == 'cancel':
                continue
            pedidos = http.request.env['sale.order.line'].sudo().search([('order_id', '=', s.id)])
            if len(pedidos) > 0:
                if s.table_number == 0:
                    t_number = 'W'
                else:
                    t_number = s.table_number
                if order_name:
                    order_name = order_name.upper()
                    if order_name == s.name:
                        orders = []
                        orders.append([s.id, s.name, str(s.order_status).upper(), pedidos, s.partner_id.name, t_number])
                        break
                    else:
                        continue
                else:
                    orders.append([s.id, s.name, str(s.order_status).upper(), pedidos, s.partner_id.name, t_number])
        #log_message(orders, do=False)
        return http.request.render('pos_sn.ptv_viewer', {'orders':orders})

    @http.route('/proceed')
    def proceed(self, **kwargs):
        '''
        Envia orden solicitada por pagina web hacia la cocina
        '''
        if 'order_id' in request.params:
            o_id = int(request.params['order_id'])
            data = {'OID':o_id}
            o_sale = http.request.env['sale.order'].search([('id', '=', o_id)])
            o_sale.update({'order_status': 'required'})
        else:
            data = {'OID':False}

        # Convertir el diccionario en una cadena JSON
        json_data = json.dumps(data)

        # Crear una respuesta JSON utilizando Response
        response = request.make_response(json_data, headers=[('Content-Type', 'application/json')])

        return response
    

class KitchenController(http.Controller):

    @http.route('/next_stage', website=True, auth='user')
    def next_stage(self, **kwargs):
        '''
        Actualiza estado de orden
        '''
        if 'order_id' in request.params:
            o_id = int(request.params['order_id'])
            o = http.request.env['sale.order'].search([('id', '=', o_id)])
            if o.order_status == 'required':
                new_state = 'preparing'
            elif o.order_status == 'preparing':
                new_state = 'ready'
            elif o.order_status == 'returned':
                new_state = 'ready'
            elif o.order_status == 'ready':
                new_state = 'dispatched'
            elif o.order_status == 'dispatched':
                new_state = 'ended'
            else:
                new_state = 'ended'
            o.update({'order_status': new_state})

            data = {'status': 'success'}
            # Convertir el diccionario en una cadena JSON
            json_data = json.dumps(data)

            # Crear una respuesta JSON utilizando Response
            response = request.make_response(json_data, headers=[('Content-Type', 'application/json')])
        else:
            data = {'status': 'not success'}
            response = request.make_response(json_data, headers=[('Content-Type', 'application/json')])

        return response

    @http.route('/previous_stage', website=True, auth='user')
    def previous_stage(self, **kwargs):
        '''
        Actualiza estado de orden
        '''
        if 'order_id' in request.params:
            o_id = int(request.params['order_id'])
            o = http.request.env['sale.order'].search([('id', '=', o_id)])
            if o.order_status == 'required':
                new_state = 'required'
            elif o.order_status == 'preparing':
                new_state = 'required'
            elif o.order_status == 'returned':
                new_state = 'preparing'
            elif o.order_status == 'ready':
                new_state = 'returned'
            elif o.order_status == 'dispatched':
                new_state = 'ready'
            else:
                new_state = 'ended'
            o.update({'order_status': new_state})

            data = {'status': 'success'}
            # Convertir el diccionario en una cadena JSON
            json_data = json.dumps(data)

            # Crear una respuesta JSON utilizando Response
            response = request.make_response(json_data, headers=[('Content-Type', 'application/json')])
        else:
            data = {'status': 'not success'}
            response = request.make_response(json_data, headers=[('Content-Type', 'application/json')])

        return response
    
    @http.route('/kitchen', website=True, auth='user')
    def kitchen_view(self, **kw):
        orders = []

        #-- Obtener las ordenes con estado de orden 'required' or 'preparing'
        sale_orders = http.request.env['sale.order'].search([('order_status', 'in', ('required', 'preparing', 'returned'))])
        for s in sale_orders:
            if s.state == 'cancel':
                continue
            pedidos = http.request.env['sale.order.line'].search([('order_id', '=', s.id)])
            if len(pedidos) > 0:
                # -- 0 es via web
                if s.table_number == 0:
                    t_number = 'W'
                else:
                    t_number = s.table_number
                orders.append([s.id, s.name, str(s.order_status).upper(), pedidos, s.partner_id.name, t_number])
        #log_message(orders, do=False)
        return http.request.render('pos_sn.ptv_kitchen', {'orders':orders})

    @http.route('/dispatch', website=True, auth='user')
    def dispatch_view(self, **kw):
        orders = []

        #-- Obtener las ordenes con estado de orden 'required' or 'preparing'
        sale_orders = http.request.env['sale.order'].search([('order_status', 'in', ('ready', 'dispatched'))])
        for s in sale_orders:
            pedidos = http.request.env['sale.order.line'].search([('order_id', '=', s.id)])
            if len(pedidos) > 0:
                if s.table_number == 0:
                    t_number = 'W'
                else:
                    t_number = s.table_number
                orders.append([s.id, s.name, str(s.order_status).upper(), pedidos, s.partner_id.name, t_number])
        #log_message(orders, do=False)
        return http.request.render('pos_sn.ptv_dispatch', {'orders':orders})

