# -*- coding: utf-8 -*-
from odoo import fields, models

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    ei_type_document_identification_id = fields.Many2one('l10n_co_fl.type_document_identification', string="Tipo de documento de identificación", required=True)
    ei_surname = fields.Char(string="Apellido", required=True)
    ei_second_surname = fields.Char(string="Segundo apellido", required=True)
    ei_first_name = fields.Char(string="Nombre", required=True)
    ei_middle_name = fields.Char(string="Segundo nombre", required=True)
