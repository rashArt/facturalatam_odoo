from odoo import models, fields, api, _
import logging
import xml.etree.ElementTree as ET
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Campos para la importación XML
    xml_file = fields.Binary(string='Archivo XML', help='Seleccione el archivo XML de la factura electrónica')
    xml_filename = fields.Char(string='Nombre del archivo')
    importing_xml = fields.Boolean(string='Importando XML', default=False, help='Indica si se está importando un XML')
    cufe_xml = fields.Char(string='CUFE del XML', help='CUFE extraído del archivo XML')

    @api.model
    def create(self, vals):
        """Sobrescribir create para transferir CUFE y documentos desde órdenes de compra"""
        move = super().create(vals)
        
        # Si es una factura de proveedor y tiene líneas vinculadas a órdenes de compra
        if move.move_type == 'in_invoice' and move.invoice_line_ids:
            for line in move.invoice_line_ids:
                if line.purchase_line_id and line.purchase_line_id.order_id.cufe_xml:
                    purchase_order = line.purchase_line_id.order_id
                    
                    # Transferir CUFE desde la orden de compra
                    cufe = purchase_order.cufe_xml
                    if cufe:
                        # Transferir tanto a ei_uuid como a cufe_xml
                        update_vals = {'cufe_xml': cufe}
                        if hasattr(move, 'ei_uuid') and not move.ei_uuid:
                            update_vals['ei_uuid'] = cufe
                        
                        move.write(update_vals)
                        _logger.info(f"CUFE transferido desde orden de compra a factura: {cufe}")
                    
                    # Transferir documentos PDF adjuntos
                    self._transfer_pdf_attachments(purchase_order, move)
                    break
        
        return move

    def write(self, vals):
        """Sobrescribir write para manejar actualizaciones de CUFE y documentos"""
        result = super().write(vals)
        
        # Si se está creando una factura y no tiene CUFE, buscar en órdenes de compra relacionadas
        if 'invoice_line_ids' in vals and self.move_type == 'in_invoice':
            for move in self:
                if not move.ei_uuid if hasattr(move, 'ei_uuid') else True:
                    for line in move.invoice_line_ids:
                        if line.purchase_line_id and line.purchase_line_id.order_id.cufe_xml:
                            purchase_order = line.purchase_line_id.order_id
                            cufe = purchase_order.cufe_xml
                            if cufe:
                                # Actualizar tanto cufe_xml como ei_uuid
                                update_vals = {'cufe_xml': cufe}
                                if hasattr(move, 'ei_uuid') and not move.ei_uuid:
                                    update_vals['ei_uuid'] = cufe
                                
                                move.write(update_vals)
                                _logger.info(f"CUFE actualizado en factura: {cufe}")
                            
                            # También transferir PDFs si es necesario
                            self._transfer_pdf_attachments(purchase_order, move)
                            break
        
        return result

    def _transfer_pdf_attachments(self, purchase_order, invoice):
        """Transfiere archivos PDF desde la orden de compra a la factura"""
        try:
            # Buscar attachments PDF de la orden de compra
            pdf_attachments = self.env['ir.attachment'].search([
                ('res_model', '=', 'purchase.order'),
                ('res_id', '=', purchase_order.id),
                ('mimetype', '=', 'application/pdf')
            ])
            
            for attachment in pdf_attachments:
                # Verificar si ya existe un attachment con el mismo nombre en la factura
                existing_attachment = self.env['ir.attachment'].search([
                    ('res_model', '=', 'account.move'),
                    ('res_id', '=', invoice.id),
                    ('name', '=', attachment.name)
                ], limit=1)
                
                if not existing_attachment:
                    # Crear una copia del attachment para la factura
                    new_attachment_vals = {
                        'name': attachment.name,
                        'type': 'binary',
                        'datas': attachment.datas,
                        'mimetype': attachment.mimetype,
                        'res_model': 'account.move',
                        'res_id': invoice.id,
                        'description': f'PDF transferido desde orden de compra {purchase_order.name}',
                        'public': False,
                    }
                    
                    new_attachment = self.env['ir.attachment'].create(new_attachment_vals)
                    _logger.info(f"PDF transferido a factura: {new_attachment.name} (ID: {new_attachment.id})")
                    
                    # Crear mensaje en el chatter de la factura
                    invoice.message_post(
                        body=f"Se ha transferido el PDF de la factura electrónica desde la orden de compra {purchase_order.name}: {attachment.name}",
                        attachment_ids=[new_attachment.id]
                    )
                else:
                    _logger.info(f"PDF ya existe en la factura: {attachment.name}")
                    
        except Exception as e:
            _logger.error(f"Error al transferir PDFs de orden de compra a factura: {str(e)}")

    def action_import_xml_wizard(self):
        """Abre el wizard para importar facturas electrónicas en facturas"""
        # Marcar como importando XML para evitar validaciones de campos obligatorios
        self.write({'importing_xml': True})
        
        return {
            'name': 'Importar Factura Electrónica',
            'type': 'ir.actions.act_window',
            'res_model': 'xml.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_account_move_id': self.id,
                'invoice_import_mode': True  # Flag para indicar que estamos en modo factura
            }
        }

    def process_xml_file(self, xml_content):
        """Procesa el archivo XML y llena la factura con los datos del XML"""
        try:
            # Parsear el XML
            root = ET.fromstring(xml_content)
            
            # Log para debug
            _logger.info(f"XML Root tag: {root.tag}")
            _logger.info(f"XML Root attrib: {root.attrib}")
            
            # Detectar tipo de XML y extraer la factura real
            invoice_root = self._extract_invoice_from_xml(root)
            
            # Definir namespaces comunes - intentar detectar automáticamente
            namespaces = self._detect_namespaces(invoice_root)
            _logger.info(f"Detected namespaces: {namespaces}")
            
            # Extraer información del proveedor
            supplier_data = self._extract_supplier_data(invoice_root, namespaces)
            _logger.info(f"Extracted supplier data: {supplier_data}")
            
            supplier = self._create_or_update_supplier(supplier_data)
            
            # Extraer información de la factura
            invoice_data = self._extract_invoice_data(invoice_root, namespaces)
            
            # Actualizar campos de la factura
            cufe = invoice_data.get('cufe', '')
            update_vals = {
                'partner_id': supplier.id,
                'ref': f"{invoice_data.get('invoice_number', '')} - {cufe}",
                'cufe_xml': cufe,  # Guardar CUFE en nuestro campo personalizado
                'importing_xml': False  # Desmarcar flag de importación
            }
            
            # También transferir al campo ei_uuid si existe (campo estándar de facturación electrónica)
            if hasattr(self, 'ei_uuid') and cufe:
                update_vals['ei_uuid'] = cufe
                _logger.info(f"CUFE transferido a ei_uuid: {cufe}")
            
            self.write(update_vals)
            
            # Procesar líneas de productos
            self._process_invoice_lines(invoice_root, namespaces)
            
            return True
            
        except ET.ParseError as e:
            self.write({'importing_xml': False})  # Desmarcar flag en caso de error
            raise UserError(f"Error al parsear el archivo XML: {str(e)}")
        except Exception as e:
            self.write({'importing_xml': False})  # Desmarcar flag en caso de error
            raise UserError(f"Error al procesar el archivo XML: {str(e)}")

    # Métodos que reutilizan funcionalidad de purchase_order.py
    def _extract_invoice_from_xml(self, root):
        """Reutiliza el método de purchase_order"""
        purchase_order = self.env['purchase.order']
        return purchase_order._extract_invoice_from_xml(root)

    def _detect_namespaces(self, root):
        """Reutiliza el método de purchase_order"""
        purchase_order = self.env['purchase.order']
        return purchase_order._detect_namespaces(root)

    def _extract_supplier_data(self, root, namespaces):
        """Reutiliza el método de purchase_order"""
        purchase_order = self.env['purchase.order']
        return purchase_order._extract_supplier_data(root, namespaces)

    def _create_or_update_supplier(self, supplier_data):
        """Reutiliza el método de purchase_order"""
        purchase_order = self.env['purchase.order']
        return purchase_order._create_or_update_supplier(supplier_data)

    def _extract_invoice_data(self, root, namespaces):
        """Reutiliza el método de purchase_order"""
        purchase_order = self.env['purchase.order']
        return purchase_order._extract_invoice_data(root, namespaces)

    def _process_invoice_lines(self, root, namespaces):
        """Procesa las líneas de la factura y crea líneas de factura"""
        # Limpiar líneas existentes
        self.invoice_line_ids.unlink()
        
        # Buscar líneas de factura con múltiples enfoques
        invoice_lines = []
        
        if namespaces:
            invoice_lines = root.findall('.//cac:InvoiceLine', namespaces)
            _logger.info(f"Líneas encontradas con namespaces: {len(invoice_lines)}")
        
        # Si no se encontraron con namespaces, buscar sin ellos
        if not invoice_lines:
            for elem in root.iter():
                if elem.tag.endswith('}InvoiceLine') or elem.tag == 'InvoiceLine':
                    invoice_lines.append(elem)
            _logger.info(f"Líneas encontradas sin namespaces: {len(invoice_lines)}")
        
        # Si aún no hay líneas, crear una línea genérica
        if not invoice_lines:
            _logger.warning("No se encontraron líneas de factura, creando línea genérica")
            self._create_generic_line()
            return
        
        for line in invoice_lines:
            line_data = self._extract_line_data(line, namespaces)
            if line_data:
                product = self._create_or_update_product(line_data)
                self._create_invoice_line(product, line_data)

    def _extract_line_data(self, line, namespaces):
        """Reutiliza el método de purchase_order"""
        purchase_order = self.env['purchase.order']
        return purchase_order._extract_line_data(line, namespaces)

    def _create_or_update_product(self, line_data):
        """Reutiliza el método de purchase_order"""
        purchase_order = self.env['purchase.order']
        return purchase_order._create_or_update_product(line_data)

    def _create_generic_line(self):
        """Crea una línea genérica cuando no se encuentran líneas en el XML"""
        # Buscar o crear producto genérico
        product_name = 'Producto Importado XML'
        
        product = self.env['product.product'].search([
            ('name', '=', product_name),
            ('default_code', '=', False)
        ], limit=1)
        
        if not product:
            product_vals = {
                'name': product_name,
                'detailed_type': 'consu',  # Crear como consumibles
                'sale_ok': True,
                'purchase_ok': True,
            }
            
            try:
                product = self.env['product.product'].create(product_vals)
                _logger.info(f"Producto genérico creado: {product.name}")
            except Exception as e:
                _logger.error(f"Error al crear producto genérico: {str(e)}")
                raise UserError(f"Error al crear producto genérico: {str(e)}")
        
        # Crear línea de factura genérica
        line_vals = {
            'move_id': self.id,
            'product_id': product.id,
            'name': product_name,
            'quantity': 1.0,
            'price_unit': 0.0,
        }
        
        self.env['account.move.line'].create(line_vals)

    def _create_invoice_line(self, product, line_data):
        """Crea una línea de factura"""
        vals = {
            'move_id': self.id,
            'product_id': product.id,
            'name': line_data.get('description', product.name),
            'quantity': line_data.get('quantity', 1.0),
            'price_unit': line_data.get('price_unit', 0.0),
        }
        
        # Buscar unidad de medida
        purchase_order = self.env['purchase.order']
        if line_data.get('unit_code'):
            unit_name = line_data.get('unit_name')
            uom = purchase_order._find_uom_by_dian_code(line_data['unit_code'], unit_name)
            if uom:
                vals['product_uom_id'] = uom.id
        
        # Procesar impuestos
        tax_ids = []
        
        if line_data.get('taxes'):
            for tax_info in line_data['taxes']:
                tax = purchase_order._find_tax_by_dian_code(
                    tax_info.get('tax_code'), 
                    tax_info.get('tax_name'), 
                    tax_info.get('percent', 0.0)
                )
                if tax:
                    tax_ids.append(tax.id)
                    _logger.info(f"Impuesto {tax.name} ({tax_info.get('percent')}%) aplicado a la línea")
        
        # Si no se aplicó ningún impuesto, aplicar IVA excluido del 0%
        if not tax_ids:
            _logger.info("No se aplicaron impuestos, buscando o creando IVA 0%")
            default_tax = purchase_order._find_tax_by_dian_code('01', 'IVA', 0.0)
            if default_tax:
                tax_ids.append(default_tax.id)
        
        if tax_ids:
            vals['tax_ids'] = [(6, 0, tax_ids)]
        
        invoice_line = self.env['account.move.line'].create(vals)
        _logger.info(f"Línea de factura creada: {invoice_line.name} con {len(tax_ids)} impuesto(s)")
        return invoice_line
