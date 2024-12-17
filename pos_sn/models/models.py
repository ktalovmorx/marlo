# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class posOrderLine(models.Model):
    '''
    Herencia y extensión del modelo pos.order.line
    '''

    _inherit = 'pos.order.line'

    order_line_done = fields.Boolean(string='IsReady', default=False)


class PosOrder(models.Model):
    '''
    Herencia y extensión del modelo pos.order
    '''

    _inherit = 'pos.order'

    kitchen_done = fields.Boolean(string='IsReady', default=False)

    def _crear_orden_de_fabricacion(self) -> None:
        """
        Método para crear la orden de fabricación para los productos de la orden POS
        """
        for line in self.lines:
            product = line.product_id

            # Verificar si el producto tiene la ruta de "Fabricación"
            if product.route_ids.filtered(lambda r: r.name == 'Fabricación'):
                # Buscar la lista de materiales (BOM) para el producto
                bom = self.env["mrp.bom"].search([("product_tmpl_id", "=", product.product_tmpl_id.id)], limit=1)
                if bom:
                    # Validar que la cantidad sea mayor que 0
                    if line.qty > 0:
                        try:
                            # Crear la orden de fabricación
                            production = self.env['mrp.production'].create({
                                'product_id': product.id,
                                'product_qty': line.qty,
                                'bom_id': bom.id,
                                'origin': self.name,  # Establecer la orden POS como origen
                            })
                            # Confirmar la orden de fabricación
                            production.action_confirm()
                        except Exception as e:
                            # Log del error para análisis
                            _logger.error(f"Error al crear la orden de fabricación para '{product.name}': {str(e)}")
                            raise ValidationError(f"Error al crear la orden de fabricación para el producto '{product.name}': {str(e)}")
                    else:
                        _logger.warning(f"Cantidad inválida para la creación de la orden de fabricación para '{product.name}'. Cantidad: {line.qty}")
                else:
                    _logger.warning(f"No se encontró BOM para el producto '{product.name}' en la orden POS.")

    def action_pos_order_paid(self):
        """
        Sobrescribir el método que se ejecuta cuando el pago de la orden es completado
        """
        # Llamar al método original para marcar la orden como pagada
        res = super(PosOrder, self).action_pos_order_paid()
        
        # Crear las órdenes de fabricación después de que se haya pagado
        self._crear_orden_de_fabricacion()

        return res

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'
    
    order_status = fields.Selection([('pending', 'Pendiente'), ('required', 'Solicitado'), ('preparing', 'Preparando'), ('returned', 'Devuelto'), ('ready', 'Listo'), ('dispatched', 'Despachado'), ('ended', 'Finalizado')], default='pending', string='Estado')
    table_number = fields.Selection(
        selection=[(str(i), str(i)) for i in range(0, 100)],
        string='Mesa',
        required=True,
        default='0')

    def action_set_required(self) -> None:
        '''
        Modifica el estado de la orden
        '''

        for record in self:
            record.order_status = 'required'

    def action_set_preparing(self) -> None:
        '''
        Modifica el estado de la orden
        '''

        for record in self:
            record.order_status = 'preparing'

    def action_set_ready(self) -> None:
        '''
        Modifica el estado de la orden
        '''

        for record in self:
            record.order_status = 'ready'

    def action_set_dispatched(self) -> None:
        '''
        Modifica el estado de la orden
        '''

        for record in self:
            record.order_status = 'dispatched'

    def action_set_ended(self) -> None:
        '''
        Modifica el estado de la orden
        '''

        for record in self:
            record.order_status = 'ended'

    @api.model
    def create(self, vals:dict) -> object:
        '''
        '''

        #-- Llamo al metodo original
        record = super(SaleOrderInherit, self).create(vals)

        #-- Obtengo el ID de la tabla actual guardada en la session del request y aplicarla al registro
        table_id = str(request.session.get('table_id'))

        if table_id not in ('None', None):
            #-- Actualizo el campo table_number del registro actual con el ID de la tabla indicado
            record.write({'table_number': table_id})

        return record
                
    def _crear_orden_de_fabricacion(self) -> None:
        """
        Método para crear la orden de fabricación para los productos de la orden POS
        """
        for order in self:
            for line in order.order_line:
                product = line.product_id

                # Verificar si el producto tiene la ruta "Fabricación"
                if product.route_ids.filtered(lambda r: r.name == 'Fabricación'):
                    # Buscar la lista de materiales (BOM) para el producto
                    bom = self.env["mrp.bom"].search([("product_tmpl_id", "=", product.product_tmpl_id.id)], limit=1)
                    if bom:
                        # Validar que la cantidad sea mayor que 0
                        if line.product_uom_qty > 0:
                            try:
                                # Crear la orden de fabricación
                                production = self.env['mrp.production'].create({
                                    'product_id': product.id,
                                    'product_qty': line.product_uom_qty,
                                    'bom_id': bom.id,
                                    'origin': order.name,  # Establecer la orden de venta como origen
                                })
                                # Confirmar la orden de fabricación
                                production.action_confirm()
                            except Exception as e:
                                # Log del error para análisis
                                _logger.error(f"Error al crear la orden de fabricación para '{product.name}': {str(e)}")
                                raise ValidationError(
                                    _(f"Error al crear la orden de fabricación para el producto '{product.name}': {str(e)}")
                                )
                        else:
                            _logger.warning(
                                f"Cantidad inválida para la creación de la orden de fabricación para '{product.name}'. Cantidad: {line.product_uom_qty}"
                            )
                    else:
                        _logger.warning(f"No se encontró BOM para el producto '{product.name}' en la orden de venta '{order.name}'.")

    def action_confirm(self) -> object:
        '''
        Sobreescritura del método de confirmación para crear la orden de fabricación
        '''

        res = super(SaleOrderInherit, self).action_confirm()
        
        # Crear posibles ordenes de fabricación luego de confirmar el pago
        if self.order_status == 'ended':
            self._crear_orden_de_fabricacion(self)
        
        return res
    

class PosSession(models.Model):
    '''
    '''
    _inherit = 'pos.session'


    def _completar_orden_cascada(self, mo) -> bool:
        """
        Completar una orden de fabricación, incluyendo las relacionadas en cascada.
        """
        ManufacturingOrder = self.env['mrp.production']

        if mo.state not in ['done', 'cancel']:
            try:
                # Buscar órdenes relacionadas con esta orden de fabricación
                related_mos = ManufacturingOrder.search([('origin', '=', mo.name)])
                for related_mo in related_mos:
                    # Completar dependencias
                    self._completar_orden_cascada(related_mo)

                # Confirmar y completar la orden actual
                if mo.state == 'confirmed':
                    # Reservar materiales
                    mo.action_assign()
                if mo.state in ['confirmed', 'progress']:
                    # Marcar como completada
                    mo.button_mark_done()
                _logger.info(f"Orden de fabricación '{mo.name}' completada correctamente.")
                return True
            except Exception as e:
                _logger.error(f"Error al completar la orden de fabricación '{mo.name}': {str(e)}")
                return False
            
    def completar_fabricacion(self) -> dict:
        """
        Buscar todas las órdenes de fabricación relacionadas con las órdenes POS
        de esta sesión y marcarlas como completadas, incluyendo en cascada.
        """

        if self.state == 'closed':
            ManufacturingOrder = self.env['mrp.production']

            total = 0
            for session in self:
                # Órdenes POS asociadas a la sesión
                for order in session.order_ids:
                    # Buscar órdenes de fabricación relacionadas con la orden POS
                    related_mos = ManufacturingOrder.search([('origin', '=', order.name)])
                    for mo in related_mos:
                        b = self._completar_orden_cascada(mo)
                        if b:
                            total += 1

            if total > 0:
                message = _(f'Se completaron %s movimientos correctamente.'%(total))
                action = {
                    'effect':{
                        'fadeout':'slow',
                        'message':message,
                        'type':'rainbow_man',
                    }
                 }
                return action
            else:
                message = _('No hay fabricaciones pendientes.')
                action = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Notificación"),
                        'type': 'warning',
                        'message': message,
                        'sticky': True,
                    },
                }
            return action
        else:
            message = _('Para completar las fabricaciones debe cerrar la sesión')
            return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _("Notificación"),
                        'type': 'danger',
                        'message': message,
                        'sticky': True,
                    },
                }

    def action_pos_session_close(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None) -> dict:
        """
        Sobrescribir el cierre de la sesión del POS para completar órdenes de fabricación 
        relacionadas y redirigir a una vista específica.
        """
        
        # Completar órdenes de fabricación relacionadas
        #self.completar_fabricacion()

        # Llamar al método original para realizar el cierre estándar
        return super(PosSession, self).action_pos_session_close(balancing_account, amount_to_balance, bank_payment_method_diffs)


class ptvModel(models.Model):
    '''
    Gestor de menús para administracion de módulos
    '''

    _name = 'pos_sn.pos_sn'
    _description = 'Gestión de puntos de venta (POS)'
    
    product_id = fields.Many2one('product.template', string='Producto', required=False)
    available_in_pos = fields.Boolean(string="Disponible en PTV", related='product_id.available_in_pos', readonly=False)
    available_in_ecommerce = fields.Boolean(string="Disponible en Web", related='product_id.is_published', readonly=False)
    available_in_autopedido = fields.Boolean(string="Disponible en Autopedido", related='product_id.self_order_available', readonly=False)
    
    def create(self, vals:dict) -> object:
        '''
        '''

        record = super(ptvModel, self).create(vals)
        return record
    
    def generate_visibility_records(self) -> None:
        '''
        '''

        products = self.env['product.template'].search([])
        for product in products:
            # Verifica si ya existe un registro. Evita duplicados!
            if not self.env['pos_sn.pos_sn'].search([('product_id', '=', product.id)]):
                self.create({'product_id': product.id})
    
    def action_generate_records(self) -> dict:
        '''
        '''
        
        self.generate_visibility_records()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }