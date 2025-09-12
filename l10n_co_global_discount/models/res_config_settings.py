from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    enable_global_discount = fields.Boolean(
        string='Habilitar descuento global',
        related='company_id.enable_global_discount',
        readonly=False
    )
    global_discount_product_id = fields.Many2one(
        'product.product',
        string='Producto de descuento predeterminado',
        domain="[('type', '=', 'service')]",
        related='company_id.global_discount_product_id',
        readonly=False
    )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env.company.enable_global_discount = self.enable_global_discount
        self.env.company.global_discount_product_id = self.global_discount_product_id

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            enable_global_discount=self.env.company.enable_global_discount,
            global_discount_product_id=self.env.company.global_discount_product_id.id,
        )
        return res

    @api.model
    def default_get(self, fields):
        res = super(ResConfigSettings, self).default_get(fields)
        if not res.get('global_discount_product_id'):
            default_product = self.env.ref('l10n_co_global_discount.product_product_global_discount', raise_if_not_found=False)
            if default_product:
                res['global_discount_product_id'] = default_product.id
        return res

    @api.onchange('enable_global_discount')
    def _onchange_enable_global_discount(self):
        if not self.enable_global_discount:
            self.global_discount_product_id = False