# -*- coding: utf-8 -*-


from odoo import fields, models


class ProductUom(models.Model):
    _inherit = "uom.uom"

    edi_unit_measure_id = fields.Many2one(comodel_name='l10n_co_fl.unit.measure',
                                          string="Unit of measure (DIAN)", ondelete='RESTRICT')
