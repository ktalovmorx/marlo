from odoo import models, api
import logging

# Configuración del logger
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s [%(filename)s:%(lineno)d]"
)
_logger = logging.getLogger(__name__)

class BusBusInherit(models.Model):
    _inherit = 'bus.bus'

    @api.model
    def _poll(self, channels, last=0):
        # Interceptar la llamada al método _poll original
        #_logger.info(f"Interceptando _poll: canales = {channels}, last = {last}")

        # Realizar acciones personalizadas aquí, si es necesario
        # ...

        # Llamar al método _poll original
        result = super(BusBusInherit, self)._poll(channels, last)

        # Realizar acciones adicionales con el resultado, si es necesario
        #_logger.info(f"Resultado de _poll: {result}")

        # Devolver el resultado
        return result