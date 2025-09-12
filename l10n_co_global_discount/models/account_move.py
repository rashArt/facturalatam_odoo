from odoo import models, fields, api

class AccountMove(models.Model):
    _inherit = 'account.move'

    global_discount_type = fields.Selection([
        ('fixed', 'Fijo'),
        ('percent', 'Porcentaje'),
    ], string='Tipo de descuento global', default='fixed')
    global_discount_amount = fields.Float('Monto de descuento global')
    active_global_discount = fields.Boolean('Descuento global activo', compute='_compute_active_global_discount')

    @api.depends('company_id.enable_global_discount')
    def _compute_active_global_discount(self):
        active_global_discount = False
        if self.company_id.enable_global_discount:
            active_global_discount = True
        self.active_global_discount = active_global_discount

    def action_apply_global_discount(self):
        for move in self:
            if move.global_discount_type and move.global_discount_amount:
                if move.global_discount_type == 'fixed':
                    discount = move.global_discount_amount
                elif move.global_discount_type == 'percent':
                    discount = move.amount_untaxed * (move.global_discount_amount / 100)

                discount_line = move.invoice_line_ids.filtered(lambda line: line.is_global_discount)
                if discount_line:
                    discount_line.price_unit = -discount
                else:
                    move.invoice_line_ids.create({
                        'move_id': move.id,
                        'product_id': self.company_id.global_discount_product_id.id,
                        'name': 'Descuento Global',
                        'price_unit': -discount,
                        'tax_ids': [(6, 0, [])],
                        'is_global_discount': True,
                    })

    def action_remove_global_discount(self):
        for move in self:
            discount_line = move.invoice_line_ids.filtered(lambda line: line.is_global_discount)
            if discount_line:
                discount_line.unlink()

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_global_discount = fields.Boolean('Es descuento global', default=False)