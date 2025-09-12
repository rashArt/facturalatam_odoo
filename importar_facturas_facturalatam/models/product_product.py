from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.constrains('default_code')
    def _check_unique_default_code(self):
        """Validar que la referencia interna sea única cuando está definida"""
        for product in self:
            if product.default_code:
                # Buscar otros productos con la misma referencia interna
                duplicate = self.search([
                    ('default_code', '=', product.default_code),
                    ('id', '!=', product.id)
                ], limit=1)
                
                if duplicate:
                    raise ValidationError(
                        f"Ya existe un producto con la referencia interna '{product.default_code}': "
                        f"{duplicate.name}. Las referencias internas deben ser únicas."
                    )

    @api.model
    def create(self, vals):
        """Override create para logging y validación adicional"""
        if vals.get('default_code'):
            _logger.info(f"Creando producto con referencia interna: {vals['default_code']}")
            
            # Verificación adicional antes de crear
            existing = self.search([('default_code', '=', vals['default_code'])], limit=1)
            if existing:
                _logger.warning(f"INTENTO DE DUPLICADO BLOQUEADO: Ya existe producto con referencia '{vals['default_code']}': {existing.name}")
                raise ValidationError(
                    f"Ya existe un producto con la referencia interna '{vals['default_code']}': "
                    f"{existing.name}. No se puede crear un duplicado."
                )
        
        return super().create(vals)

    def write(self, vals):
        """Override write para validación adicional de referencia interna"""
        if vals.get('default_code'):
            for product in self:
                _logger.info(f"Actualizando referencia interna del producto '{product.name}' a: {vals['default_code']}")
                
                # Verificar que no exista otro producto con esa referencia
                existing = self.search([
                    ('default_code', '=', vals['default_code']),
                    ('id', '!=', product.id)
                ], limit=1)
                
                if existing:
                    _logger.warning(f"INTENTO DE DUPLICADO BLOQUEADO: No se puede asignar referencia '{vals['default_code']}' a '{product.name}' porque ya existe en '{existing.name}'")
                    raise ValidationError(
                        f"No se puede asignar la referencia interna '{vals['default_code']}' "
                        f"al producto '{product.name}' porque ya existe en el producto: {existing.name}"
                    )
        
        return super().write(vals)
