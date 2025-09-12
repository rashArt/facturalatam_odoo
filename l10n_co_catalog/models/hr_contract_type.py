# -*- coding: utf-8 -*-
from odoo import fields, models

class HrContractType(models.Model):
    _inherit = 'hr.contract.type'

    ei_contract_type_id = fields.Selection([
        ('1', 'Término Fijo'),
        ('2', 'Término Indefinido'),
        ('3', 'Obra o Labor'),
        ('4', 'Aprendizaje'),
        ('5', 'Prácticas')
    ], string="Equivalente Nómina Electrónica", help="Equivalente del tipo de contrato para nómina electrónica.")
