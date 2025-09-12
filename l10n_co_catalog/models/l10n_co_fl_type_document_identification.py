from odoo import models, fields

class L10nCoFlDocumentTypeIdentification(models.Model):
    _name = 'l10n_co_fl.type_document_identification'
    _description = 'Type Document Identification'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
