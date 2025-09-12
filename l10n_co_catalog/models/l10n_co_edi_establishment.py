from odoo import models, fields

class EdiEstablishment(models.Model):
    _name = "l10n_co_edi.establishment"
    _description = "Establishment Information for EDI"

    name = fields.Char(string="Nombre del establecimiento", required=True)
    address = fields.Char(string="Dirección del establecimiento", required=True)
    phone = fields.Char(string="Teléfono del establecimiento", required=True)
    municipality_id = fields.Many2one('l10n_co_fl.municipality', string="Municipio" ,required=True)
    email = fields.Char(string="Correo electrónico del establecimiento", required=True)
    branch_company_id = fields.Many2one(
        'res.company',
        string="Sucursal (Establecimiento)",
        help="Sucursal asociada"
    )
