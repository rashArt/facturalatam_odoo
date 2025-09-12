from odoo import models, fields

class CoRequestEdi(models.Model):
    _name = 'co.request.edi'
    _description = 'Request EDI para Colombia'

    invoice_id = fields.Many2one('account.move', string='Factura', ondelete='cascade')
    invoic_name = fields.Char(string='Nombre de la Factura' , related='invoice_id.name')
    status = fields.Selection([('pending', 'Pending'), ('success', 'Success'), ('error', 'Error')], string='Status', default='pending')
    response_message = fields.Text(string='Response Message')
    response_xml = fields.Text(string='Response XML')
    response_xml_filename = fields.Char(string='Response XML Filename')
    response_xml_binary = fields.Binary(string='Response XML Binary')
    co_log_edi_ids = fields.One2many('co.log.edi', 'request_id', string='Logs EDI')



    def action_open_document_invoice_id(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
