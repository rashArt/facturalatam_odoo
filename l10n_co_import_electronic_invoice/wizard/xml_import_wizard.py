from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import zipfile
import io
import logging

_logger = logging.getLogger(__name__)


class XmlImportWizard(models.TransientModel):
    _name = 'xml.import.wizard'
    _description = 'Wizard para importar XML de factura electrónica'

    xml_file = fields.Binary(string='Archivo de Factura', required=True, help='Seleccione el archivo XML de la factura electrónica o un archivo ZIP que contenga el XML y PDF')
    xml_filename = fields.Char(string='Nombre del archivo')
    purchase_order_id = fields.Many2one('purchase.order', string='Orden de Compra')
    account_move_id = fields.Many2one('account.move', string='Factura')
    
    @api.onchange('account_move_id', 'purchase_order_id')
    def _onchange_target_record(self):
        """Asegurar que solo uno de los dos campos esté lleno"""
        if self.account_move_id and self.purchase_order_id:
            if self._context.get('invoice_import_mode'):
                self.purchase_order_id = False
            else:
                self.account_move_id = False

    def action_import_xml(self):
        """Importa el archivo XML o ZIP y procesa los datos"""
        if not self.xml_file:
            raise UserError("Debe seleccionar un archivo")
        
        # Verificar que se haya seleccionado un registro de destino
        if not self.purchase_order_id and not self.account_move_id:
            raise UserError("Debe especificar una orden de compra o una factura")
        
        # Decodificar el archivo
        file_content = base64.b64decode(self.xml_file)
        xml_content = None
        pdf_content = None
        pdf_filename = None
        
        # Detectar el tipo de archivo
        if self.xml_filename and self.xml_filename.lower().endswith('.zip'):
            _logger.info(f"Procesando archivo ZIP: {self.xml_filename}")
            xml_content, pdf_content, pdf_filename = self._extract_from_zip(file_content)
        else:
            _logger.info(f"Procesando archivo XML: {self.xml_filename}")
            xml_content = file_content
        
        if not xml_content:
            raise UserError("No se pudo extraer el contenido XML del archivo")
        
        # Procesar según el tipo de registro
        if self.purchase_order_id:
            target_record = self.purchase_order_id
            _logger.info(f"Procesando XML en orden de compra: {target_record.name}")
        else:
            target_record = self.account_move_id
            _logger.info(f"Procesando XML en factura: {target_record.name}")
        
        # Guardar el archivo original en el registro destino
        target_record.write({
            'xml_file': self.xml_file,
            'xml_filename': self.xml_filename
        })
        
        # Procesar el archivo XML
        target_record.process_xml_file(xml_content)
        
        # Si hay un PDF, adjuntarlo como documento
        pdf_attachment = None
        if pdf_content and pdf_filename:
            if self.purchase_order_id:
                pdf_attachment = self._attach_pdf_to_purchase_order(pdf_content, pdf_filename)
            else:
                pdf_attachment = self._attach_pdf_to_invoice(pdf_content, pdf_filename)
        
        # Guardar referencia del PDF en el registro destino si se creó
        if pdf_attachment:
            if hasattr(target_record, 'pdf_attachment_id'):
                target_record.write({
                    'pdf_attachment_id': pdf_attachment.id,
                    'pdf_filename': pdf_filename
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def _extract_from_zip(self, zip_content):
        """Extrae XML y PDF de un archivo ZIP"""
        xml_content = None
        pdf_content = None
        pdf_filename = None
        
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zip_file:
                file_list = zip_file.namelist()
                _logger.info(f"Archivos en ZIP: {file_list}")
                
                # Buscar archivo XML
                xml_files = [f for f in file_list if f.lower().endswith('.xml')]
                if xml_files:
                    xml_filename = xml_files[0]  # Tomar el primer XML
                    xml_content = zip_file.read(xml_filename)
                    _logger.info(f"XML extraído: {xml_filename}")
                
                # Buscar archivo PDF
                pdf_files = [f for f in file_list if f.lower().endswith('.pdf')]
                if pdf_files:
                    pdf_filename = pdf_files[0]  # Tomar el primer PDF
                    pdf_content = zip_file.read(pdf_filename)
                    _logger.info(f"PDF extraído: {pdf_filename}")
                
        except zipfile.BadZipFile:
            raise UserError("El archivo ZIP está corrupto o no es válido")
        except Exception as e:
            raise UserError(f"Error al extraer archivos del ZIP: {str(e)}")
        
        if not xml_content:
            raise UserError("No se encontró archivo XML en el ZIP")
        
        return xml_content, pdf_content, pdf_filename

    def _attach_pdf_to_purchase_order(self, pdf_content, pdf_filename):
        """Adjunta el PDF como documento a la orden de compra"""
        try:
            # Verificar si ya existe un attachment con el mismo nombre
            existing_attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'purchase.order'),
                ('res_id', '=', self.purchase_order_id.id),
                ('name', '=', pdf_filename)
            ], limit=1)
            
            if existing_attachment:
                _logger.info(f"PDF ya existe, actualizando: {pdf_filename}")
                existing_attachment.write({
                    'datas': base64.b64encode(pdf_content),
                })
                return existing_attachment
            
            attachment_vals = {
                'name': pdf_filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'mimetype': 'application/pdf',
                'res_model': 'purchase.order',
                'res_id': self.purchase_order_id.id,
                'description': 'PDF de factura electrónica importada',
                'public': False,  # Para que aparezca en el chatter
            }
            
            attachment = self.env['ir.attachment'].create(attachment_vals)
            _logger.info(f"PDF adjuntado a orden de compra: {attachment.name} (ID: {attachment.id})")
            
            # Crear un mensaje en el chatter para notificar el adjunto
            self.purchase_order_id.message_post(
                body=f"Se ha adjuntado el archivo PDF de la factura electrónica: {pdf_filename}",
                attachment_ids=[attachment.id]
            )
            
            return attachment
            
        except Exception as e:
            _logger.error(f"Error al adjuntar PDF: {str(e)}")
            # No lanzar error, solo registrar el problema

    def _attach_pdf_to_invoice(self, pdf_content, pdf_filename):
        """Adjunta el PDF como documento a la factura"""
        try:
            # Verificar si ya existe un attachment con el mismo nombre
            existing_attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', self.account_move_id.id),
                ('name', '=', pdf_filename)
            ], limit=1)
            
            if existing_attachment:
                _logger.info(f"PDF ya existe, actualizando: {pdf_filename}")
                existing_attachment.write({
                    'datas': base64.b64encode(pdf_content),
                })
                return existing_attachment
            
            attachment_vals = {
                'name': pdf_filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'mimetype': 'application/pdf',
                'res_model': 'account.move',
                'res_id': self.account_move_id.id,
                'description': 'PDF de factura electrónica importada',
                'public': False,  # Para que aparezca en el chatter
            }
            
            attachment = self.env['ir.attachment'].create(attachment_vals)
            _logger.info(f"PDF adjuntado a factura: {attachment.name} (ID: {attachment.id})")
            
            # Crear un mensaje en el chatter para notificar el adjunto
            self.account_move_id.message_post(
                body=f"Se ha adjuntado el archivo PDF de la factura electrónica: {pdf_filename}",
                attachment_ids=[attachment.id]
            )
            
            return attachment
            
        except Exception as e:
            _logger.error(f"Error al adjuntar PDF a factura: {str(e)}")
            # No lanzar error, solo registrar el problema
