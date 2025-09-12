from odoo import models, fields

class InvoiceTemplate(models.Model):
    _name = 'invoice.template'
    _description = 'Invoice Templates'

    api_template_id = fields.Char("API Template ID", required=True)
    name = fields.Char("Template Name", required=True)
    image_url = fields.Char("Template Image URL", required=True)