from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    enable_global_discount = fields.Boolean(string='Habilitar Descuento Global')
    global_discount_product_id = fields.Many2one(
        'product.product',
        string='Producto de Descuento Predeterminado',
        domain="[('type', '=', 'service')]"
    )
