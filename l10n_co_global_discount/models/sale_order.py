from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    global_discount_type = fields.Selection([
        ('fixed', 'Fixed'),
        ('percent', 'Percentage'),
    ], string='Global Discount Type', default='fixed')
    global_discount_amount = fields.Float('Global Discount Amount')

    def action_apply_global_discount(self):
        for order in self:
            if order.global_discount_type and order.global_discount_amount:
                if order.global_discount_type == 'fixed':
                    discount = order.global_discount_amount
                elif order.global_discount_type == 'percent':
                    discount = order.amount_untaxed * (order.global_discount_amount / 100)

                discount_line = order.order_line.filtered(lambda line: line.is_global_discount)
                if discount_line:
                    discount_line.price_unit = -discount
                else:
                    order.order_line.create({
                        'order_id': order.id,
                        'product_id': int(self.env['ir.config_parameter'].sudo().get_param('sale.default_discount_product_id')),
                        'name': 'Global Discount',
                        'price_unit': -discount,
                        'is_global_discount': True,
                    })

    def action_remove_global_discount(self):
        for order in self:
            discount_line = order.order_line.filtered(lambda line: line.is_global_discount)
            if discount_line:
                discount_line.unlink()

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_global_discount = fields.Boolean('Is Global Discount', default=False)