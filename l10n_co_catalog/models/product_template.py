# -*- coding: utf-8 -*-


from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brandname = fields.Char(string='Marca', required=False)
    modelname = fields.Char(string='Modelo', required=False)

    def _get_default_type_item_identification(self):
        if not self.env['l10n_co_fl.type.item.identification'].search_count([]):
            self.env['res.company'].init_csv_data('l10n_co_catalog.l10n_co_fl.type_item_identification')
        return 4
    type_item_identification_id = fields.Many2one('l10n_co_fl.type.item.identification', default=lambda self: self._get_default_type_item_identification(),string="Tipo de Identificación de Item")