# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.http import request
from odoo.exceptions import ValidationError
import logging
from odoo import tools
import re

# Configuración del logger
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]"
)
_logger = logging.getLogger(__name__)

class Website(models.Model):
    '''
    '''
    _inherit = 'website'

    # self.env.uid for ir.rule groups on menu
    @tools.ormcache('self.env.uid', 'self.id', cache='templates')
    def _get_menu_ids(self):
        return self.env['website.menu'].search([('website_id', '=', self.id)]).ids

    @tools.ormcache('self.env.uid', 'self.id', cache='templates')
    def is_menu_cache_disabled(self):
        """
        Checks if the website menu contains a record like url.
        :return: True if the menu contains a record like url
        """
        return any(self.env['website.menu'].browse(self._get_menu_ids()).filtered(
            lambda menu: menu.url and re.search(r"[/](([^/=?&]+-)?[0-9]+)([/]|$)", menu.url))
        )


class IrHttp(models.AbstractModel):
    '''
    '''
    _inherit = 'ir.http'

    @classmethod
    def _get_base_url(cls):
        base_url = request.env['ir.config_parameter'].sudo().get_param('fixed_url')
        request.env['ir.config_parameter'].sudo().set_param('web.base.url', base_url)
        return base_url
        #return super(IrHttp, cls)._get_base_url()


class InheritBaseModel(models.AbstractModel):
    '''
    '''
    _inherit = 'base'

    #-- EN EL ARCHIVO models.py
    def get_base_url(self):
        """ Return rooturl for a specific record.

        By default, it returns the ir.config.parameter of base_url
        but it can be overridden by model.

        :return: the base url for this record
        :rtype: str
        """
        if len(self) > 1:
            raise ValueError("Expected singleton or no record: %s" % self)
        
        base_url = self.env['ir.config_parameter'].sudo().get_param('fixed_url')
        return base_url
     
class InheritResUsers(models.Model):
    '''
    '''
    _inherit = 'res.users'

    @classmethod
    def authenticate(cls, db, login, password, user_agent_env):
        """Verifies and returns the user ID corresponding to the given
        ``login`` and ``password`` combination, or False if there was
        no matching user.
            :param str db: the database on which user is trying to authenticate
            :param str login: username
            :param str password: user password
            :param dict user_agent_env: environment dictionary describing any
            relevant environment attributes
        """
        uid = cls._login(db, login, password, user_agent_env=user_agent_env)
        if user_agent_env and user_agent_env.get('base_location'):
            with cls.pool.cursor() as cr:
                env = api.Environment(cr, uid, {})
                if env.user.has_group('base.group_system'):
                    # Successfully logged in as system user!
                    # Attempt to guess the web base url...
                    try:
                        #base = user_agent_env['base_location']
                        ICP = env['ir.config_parameter']
                        base = ICP.get_param('fixed_url')
                        if not ICP.get_param('web.base.url.freeze'):
                            ICP.set_param('web.base.url', base)
                        else:
                            ICP.set_param('web.base.url', base)
                    except Exception:
                        _logger.exception("Failed to update web.base.url configuration parameter")
                    try:
                        #base = user_agent_env['base_location']
                        ICP = env['ir.config_parameter']
                        base = ICP.get_param('fixed_url')
                        # Verificar si el usuario actual es anónimo (no autenticado)
                        if env.user and not env.user.id:  # env.user.id es None para usuarios anónimos
                            # Verificar si el parámetro web.base.url.freeze no está configurado
                            if not ICP.get_param('web.base.url.freeze'):
                                # Establecer el parámetro web.base.url con la ubicación base
                                ICP.set_param('web.base.url', base)
                            else:
                                ICP.set_param('web.base.url', base)
                    except Exception:
                        _logger.exception("Failed to update web.base.url configuration parameter")
        return uid


class ProductTemplateInherit(models.Model):
    '''
    '''

    _inherit = 'product.template'

    notes = fields.Text(string='Notas', default='-')
    
class HrExpense(models.Model):
    '''
    '''
    _inherit = 'hr.expense'

    sale_order_id = fields.Many2one(
        'sale.order', 
        string='Sale Order', 
        help='Related Sale Order'
    )
    

class SaleOrderLine(models.Model):
    '''
    '''
    _inherit = 'sale.order.line'

    margin = fields.Float(string='Margen', compute='_computar_margen', store= True)

    @api.depends('product_id', 'product_uom_qty', 'price_unit')
    def _computar_margen(self):
        for line in self:
            cost = line.product_id.standard_price
            line.margin = (line.price_unit - cost) * line.product_uom_qty


class saleOrder(models.Model):
    '''
    Herencia y extensión del modelo res.partner
    '''

    _inherit = 'sale.order'

    margin = fields.Float(string='Margen', compute='_computar_margen', store= True)
    expense_count = fields.Integer(string='Expense Count', compute='_compute_expense_count')
        
    # Remaining ux fields (not computed, not stored)
    show_update_fpos = fields.Boolean(
        string="Has Fiscal Position Changed", store=False)  # True if the fiscal position was changed
    has_active_pricelist = fields.Boolean(
        compute='_compute_has_active_pricelist')
    show_update_pricelist = fields.Boolean(
        string="Has Pricelist Changed", store=False)  # True if the pricelist was changed

    def call_add_from_catalog(self):
        '''
        Método que llama al método action_add_from_catalog en cada línea de pedido (sale.order.line)
        '''
        for line in self.order_line:
            if hasattr(line, 'action_add_from_catalog'):
                line.action_add_from_catalog()
            else:
                raise ValueError("El método 'action_add_from_catalog' no existe en sale.order.line")
        return True  # Opcionalmente podrías redireccionar o realizar otra acción
    
    @api.depends('order_line')
    def _compute_expense_count(self):
        for order in self:
            # Calcular el número de gastos asociados
            expense_count = self.env['hr.expense'].search_count([('sale_order_id', '=', order.id)])
            order.expense_count = expense_count

    @api.depends('order_line')
    def _computar_margen(self):
        for order in self:
            #order.margin = sum(line.margin for line in order.order_line)
            order.margin = order.amount_total * order.margin_percent


class resPartner(models.Model):
    '''
    Herencia y extensión del modelo res.partner
    '''
    _inherit = 'res.partner'
    _sql_constraints = [('unique_1', 'unique(dni_card)', 'Cédula única'),
                        ('unique_2', 'unique(license_id)', 'Licencia única'),
                        ('unique_3', 'unique(passport_id)', 'Pasaporte único'),
                        ('unique_4', 'unique(user_card)', 'Codigo de tarjeta unico'),
                        ('unique_5', 'unique(card_barcode)', 'Barcode unico')
                        ]

    email = fields.Char(string='Correo Electrónico', required=False)
    user_card = fields.Char(string='Tarjeta')
    card_barcode = fields.Char(string='RFIDCode')
    dni_card = fields.Char(string="Cédula")
    passport_id = fields.Char(string="Pasaporte")
    license_id = fields.Char(string="Licencia")
    user_type = fields.Selection([('usuario', 'Usuario'), 
                                  ('proveedor', 'Proveedor'), 
                                  ('doctor', 'Doctor'), 
                                  ('responsable', 'Responsable'), 
                                  ('recepcion', 'Recepcionista'), 
                                  ('cajero', 'Cajero'), 
                                  ('empleado', 'Empleado'), 
                                  ('cliente', 'Cliente'), 
                                  ('administrador', 'Administrador'), 
                                  ('paciente', 'Paciente')], 
                                  default='usuario', 
                                  string="Tipo de Usuario")


class accountMove(models.Model):
    '''
    Herencia y extensión del modelo account.move (facturas)
    '''
    _inherit = 'account.move'

    code_ncf = fields.Char(string="NCF", required=False)
    revoked_ncf = fields.Char(string="NCF-Old", help='NCF anterior', required=False)
    contract_name = fields.Char(string="Contrato", required=False)

    @api.model
    def update_base_url(self):
        '''Actualiza la URL base'''

        try:
            # Obtener el valor del parámetro 'fixed_url'
            freezed_url = self.env['ir.config_parameter'].sudo().get_param('fixed_url')
            self.env['ir.config_parameter'].sudo().set_param('web.base.url', freezed_url)
        except Exception as e:
            _logger.error("Error al actualizar el parámetro web.base.url: %s", e)
            # Manejar la excepción según sea necesario

    @api.model
    def read(self, fields=None, load='_classic_read'):
        # Lógica personalizada antes de leer los datos
        res = super(accountMove, self).read(fields, load)

        self.update_base_url()

        # Lógica personalizada después de leer los datos
        return res
    
    def action_invoice_sent(self):
        """
        This method is called when an invoice is sent.
        Sobre escribe el método action_invoice_sent de account.move para que se cambie el parametro web.base.url por fixed_url
        Esto debido a que cuando ejecutamos un contenedor docker expuesto mediante un dominio externo el parametro web.base.url se
        queda apuntando al dominio local del contenedor como http://localhost:{{port}}/
        """
        res = super(accountMove, self).action_invoice_sent()

        self.update_base_url()

        return res
    
    def action_apply_ncf(self):
        '''
        Asigna un NCF a la transacción
        '''

        #-- Busca NCF que no esten utilizados
        free_ncf = self.env['ncf.model'].search([('is_used', '=', False)], order='code asc', limit=1)
        if free_ncf:
            # Asignar el cliente encontrado al campo Many2one
            self.code_ncf = free_ncf[0].code
            free_ncf[0].is_used = True
        else:
            self.code_ncf = ''
            raise ValidationError('Ups, no dispones de NCF. Solicita otros y vuelve a intentarlo.')

    def action_revoke_ncf(self):
        '''
        Deselecciona el NCF aplicado a la transacción
        '''

        if self.code_ncf:
            free_ncf = self.env['ncf.model'].search([('code', '=', self.code_ncf)], limit=1)
            free_ncf.is_used = True
            self.revoked_ncf = self.code_ncf
            self.code_ncf = ''
