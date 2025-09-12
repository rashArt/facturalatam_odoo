from odoo import models, fields, api
from odoo.exceptions import UserError
import xml.etree.ElementTree as ET
import base64
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    xml_file = fields.Binary(string='Archivo XML', help='Seleccione el archivo XML de la factura electrónica')
    xml_filename = fields.Char(string='Nombre del archivo')
    importing_xml = fields.Boolean(string='Importando XML', default=False, help='Indica si se está importando un XML')
    cufe_xml = fields.Char(string='CUFE del XML', help='CUFE extraído del archivo XML')
    pdf_attachment_id = fields.Many2one('ir.attachment', string='PDF Adjunto', help='PDF de la factura electrónica')
    pdf_filename = fields.Char(string='Nombre del PDF', help='Nombre del archivo PDF adjunto')
    
    # Sobrescribir partner_id para hacerlo no obligatorio durante importación
    partner_id = fields.Many2one(
        'res.partner', 
        string='Vendor', 
        required=False,  # Quitamos required=True por defecto
        change_default=True, 
        tracking=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="You can find a vendor by its Name, TIN, Email or Internal Reference."
    )

    @api.constrains('partner_id', 'state')
    def _check_partner_id_required(self):
        """Validar que partner_id sea obligatorio excepto durante importación XML"""
        for record in self:
            # No validar si estamos importando XML
            if record.importing_xml:
                continue
            # Si no hay proveedor y no está en borrador, es un error
            if not record.partner_id and record.state not in ('draft',):
                raise UserError("El proveedor es obligatorio para confirmar la orden de compra.")

    def action_import_xml_wizard(self):
        """Abre el wizard para importar facturas electrónicas"""
        # Marcar como importando XML para evitar validaciones de campos obligatorios
        self.write({'importing_xml': True})
        
        return {
            'name': 'Importar Factura Electrónica',
            'type': 'ir.actions.act_window',
            'res_model': 'xml.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_purchase_order_id': self.id}
        }

    def process_xml_file(self, xml_content):
        """Procesa el archivo XML y crea/actualiza proveedor, productos y líneas"""
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
            
            # Actualizar campos de la orden de compra
            self.write({
                'partner_id': supplier.id,
                'partner_ref': f"{invoice_data.get('invoice_number', '')} - {invoice_data.get('cufe', '')}",
                'cufe_xml': invoice_data.get('cufe', ''),  # Guardar CUFE
                'importing_xml': False  # Desmarcar flag de importación
            })
            
            # Procesar líneas de productos
            self._process_invoice_lines(invoice_root, namespaces)
            
            return True
            
        except ET.ParseError as e:
            self.write({'importing_xml': False})  # Desmarcar flag en caso de error
            raise UserError(f"Error al parsear el archivo XML: {str(e)}")
        except Exception as e:
            self.write({'importing_xml': False})  # Desmarcar flag en caso de error
            raise UserError(f"Error al procesar el archivo XML: {str(e)}")

    def _extract_invoice_from_xml(self, root):
        """Extrae la factura real del XML, manejando diferentes formatos"""
        _logger.info(f"Procesando XML tipo: {root.tag}")
        
        # Caso 1: Es directamente una factura (Invoice)
        if root.tag.endswith('}Invoice') or root.tag == 'Invoice':
            _logger.info("XML es directamente una factura")
            return root
        
        # Caso 2: Es un AttachedDocument que contiene la factura en Description
        if root.tag.endswith('}AttachedDocument') or root.tag == 'AttachedDocument':
            _logger.info("XML es un AttachedDocument, buscando factura interna")
            
            # Buscar Description que contenga la factura
            for description in root.iter():
                if description.tag.endswith('}Description') or description.tag == 'Description':
                    if description.text and '<Invoice' in description.text:
                        _logger.info("Encontrada factura dentro de Description")
                        try:
                            # Parsear el XML interno
                            invoice_xml = description.text.strip()
                            return ET.fromstring(invoice_xml)
                        except ET.ParseError as e:
                            _logger.warning(f"Error parseando factura interna: {e}")
                            continue
        
        # Caso 3: Buscar cualquier elemento Invoice en el árbol
        for elem in root.iter():
            if elem.tag.endswith('}Invoice') or elem.tag == 'Invoice':
                _logger.info("Encontrado elemento Invoice en el árbol")
                return elem
        
        # Caso 4: Si no encontramos Invoice, usar el root original
        _logger.warning("No se encontró elemento Invoice, usando root original")
        return root

    def _detect_namespaces(self, root):
        """Detecta automáticamente los namespaces del XML"""
        namespaces = {}
        
        # Obtener namespaces del root
        for prefix, uri in root.nsmap.items() if hasattr(root, 'nsmap') else {}:
            if prefix:
                namespaces[prefix] = uri
        
        # Namespaces comunes por defecto
        default_namespaces = {
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
            'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
        }
        
        # Si no hay namespaces detectados, usar los por defecto
        if not namespaces:
            namespaces = default_namespaces
        else:
            # Agregar los que falten
            for prefix, uri in default_namespaces.items():
                if prefix not in namespaces:
                    namespaces[prefix] = uri
        
        return namespaces

    def _extract_supplier_data(self, root, namespaces):
        """Extrae datos del proveedor del XML"""
        supplier_data = {}
        
        _logger.info("Iniciando extracción de datos del proveedor")
        
        # Lista de posibles ubicaciones del proveedor
        supplier_locations = [
            './/cac:AccountingSupplierParty/cac:Party',
            './/cac:AccountingSupplierParty',
            './/cac:SupplierParty/cac:Party',
            './/cac:SupplierParty',
            './/cac:SenderParty',
            './/cac:Party'
        ]
        
        supplier_party = None
        accounting_supplier_party = None  # Para buscar AdditionalAccountID
        
        # Intentar cada ubicación con namespaces
        if namespaces:
            for location in supplier_locations:
                found_element = root.find(location, namespaces)
                if found_element is not None:
                    if location.endswith('/cac:Party'):
                        # Si encontramos Party dentro de AccountingSupplierParty, guardar ambos
                        supplier_party = found_element
                        # Buscar el AccountingSupplierParty padre
                        accounting_supplier_party = root.find('.//cac:AccountingSupplierParty', namespaces)
                    else:
                        supplier_party = found_element
                        if 'AccountingSupplier' in location:
                            accounting_supplier_party = found_element
                    _logger.info(f"Proveedor encontrado en: {location}")
                    break
        
        # Si no se encuentra con namespaces, buscar sin ellos
        if supplier_party is None:
            supplier_elements = ['AccountingSupplierParty', 'SupplierParty', 'SenderParty', 'Party']
            for elem in root.iter():
                for supplier_elem in supplier_elements:
                    if elem.tag.endswith('}' + supplier_elem) or elem.tag == supplier_elem:
                        # Si es AccountingSupplierParty o SupplierParty, buscar Party dentro
                        if supplier_elem in ['AccountingSupplierParty', 'SupplierParty']:
                            accounting_supplier_party = elem  # Guardar el elemento completo
                            for child in elem:
                                if child.tag.endswith('}Party') or child.tag == 'Party':
                                    supplier_party = child
                                    break
                        else:
                            supplier_party = elem
                        
                        if supplier_party is not None:
                            _logger.info(f"Proveedor encontrado sin namespaces: {supplier_elem}")
                            break
                if supplier_party is not None:
                    break
        
        if supplier_party is not None:
            _logger.info("Procesando datos del proveedor encontrado")
            
            # Extraer nombre del proveedor con múltiples enfoques
            name = self._extract_supplier_name(supplier_party, namespaces)
            if name:
                supplier_data['name'] = name
            
            # Extraer información de dirección
            self._extract_address_data(supplier_party, supplier_data, namespaces)
            
            # Extraer información de contacto
            self._extract_contact_data(supplier_party, supplier_data, namespaces)
            
            # Extraer información fiscal (NIT, etc.)
            # Pasar tanto el Party como el AccountingSupplierParty para tener acceso completo
            self._extract_supplier_tax_data(supplier_party, supplier_data, namespaces, accounting_supplier_party)
        
        else:
            _logger.warning("No se encontró elemento de proveedor en el XML")
            # Como último recurso, buscar cualquier RegistrationName o Name
            name = self._find_any_name(root)
            if name:
                supplier_data['name'] = name
        
        return supplier_data

    def _extract_supplier_name(self, supplier_party, namespaces):
        """Extrae el nombre del proveedor con múltiples enfoques"""
        name_locations = [
            './/cac:PartyName/cbc:Name',
            './/cbc:RegistrationName',
            './/cac:PartyLegalEntity/cbc:RegistrationName',
            './/cac:PartyTaxScheme/cbc:RegistrationName',
            './/cbc:Name'
        ]
        
        # Buscar con namespaces
        if namespaces:
            for location in name_locations:
                elem = supplier_party.find(location, namespaces)
                if elem is not None and elem.text and elem.text.strip():
                    _logger.info(f"Nombre encontrado en: {location} -> {elem.text}")
                    return elem.text.strip()
        
        # Buscar sin namespaces
        name_tags = ['RegistrationName', 'Name']
        for tag in name_tags:
            for elem in supplier_party.iter():
                if (elem.tag.endswith('}' + tag) or elem.tag == tag) and elem.text and elem.text.strip():
                    # Evitar números puros o textos muy cortos
                    text = elem.text.strip()
                    if len(text) > 3 and not text.isdigit():
                        _logger.info(f"Nombre encontrado sin namespaces: {tag} -> {text}")
                        return text
        
        return None

    def _extract_supplier_tax_data(self, supplier_party, supplier_data, namespaces, accounting_supplier_party=None):
        """Extrae datos fiscales del proveedor"""
        _logger.info("Iniciando extracción de datos fiscales")
        
        # Buscar CompanyID para identification_co_number y document type
        tax_locations = [
            './/cac:PartyTaxScheme/cbc:CompanyID',
            './/cbc:CompanyID',
            'cac:PartyTaxScheme/cbc:CompanyID',  # Buscar directamente en el elemento
            'cbc:CompanyID'
        ]
        
        if namespaces:
            for location in tax_locations:
                elem = supplier_party.find(location, namespaces)
                if elem is not None and elem.text and elem.text.strip():
                    # identification_co_number: valor del CompanyID
                    supplier_data['identification_co_number'] = elem.text.strip()
                    _logger.info(f"Encontrado identification_co_number: {supplier_data['identification_co_number']}")
                    
                    # document_type_code: valor de schemeName
                    scheme_name = elem.get('schemeName')
                    if scheme_name:
                        supplier_data['document_type_code'] = scheme_name
                        _logger.info(f"Encontrado document_type_code: {supplier_data['document_type_code']}")
                    break
        
        # Buscar sin namespaces
        if not supplier_data.get('identification_co_number'):
            for elem in supplier_party.iter():
                if (elem.tag.endswith('}CompanyID') or elem.tag == 'CompanyID') and elem.text and elem.text.strip():
                    supplier_data['identification_co_number'] = elem.text.strip()
                    _logger.info(f"Encontrado identification_co_number (sin ns): {supplier_data['identification_co_number']}")
                    
                    scheme_name = elem.get('schemeName')
                    if scheme_name:
                        supplier_data['document_type_code'] = scheme_name
                        _logger.info(f"Encontrado document_type_code (sin ns): {supplier_data['document_type_code']}")
                    break
        
        # Buscar TaxLevelCode para liability y regime
        tax_level_locations = [
            './/cac:PartyTaxScheme/cbc:TaxLevelCode',
            './/cbc:TaxLevelCode',
            'cac:PartyTaxScheme/cbc:TaxLevelCode',  # Buscar directamente en el elemento
            'cbc:TaxLevelCode'
        ]
        
        if namespaces:
            for location in tax_level_locations:
                elem = supplier_party.find(location, namespaces)
                if elem is not None and elem.text and elem.text.strip():
                    # liability_code: valor del TaxLevelCode
                    supplier_data['liability_code'] = elem.text.strip()
                    _logger.info(f"Encontrado liability_code: {supplier_data['liability_code']}")
                    
                    # regime_code: valor de listName
                    list_name = elem.get('listName')
                    if list_name:
                        supplier_data['regime_code'] = list_name
                        _logger.info(f"Encontrado regime_code: {supplier_data['regime_code']}")
                    break
        
        # Buscar sin namespaces para TaxLevelCode
        if not supplier_data.get('liability_code'):
            for elem in supplier_party.iter():
                if (elem.tag.endswith('}TaxLevelCode') or elem.tag == 'TaxLevelCode') and elem.text and elem.text.strip():
                    supplier_data['liability_code'] = elem.text.strip()
                    _logger.info(f"Encontrado liability_code (sin ns): {supplier_data['liability_code']}")
                    
                    list_name = elem.get('listName')
                    if list_name:
                        supplier_data['regime_code'] = list_name
                        _logger.info(f"Encontrado regime_code (sin ns): {supplier_data['regime_code']}")
                    break
        
        # Buscar AdditionalAccountID para organization type
        # Primero intentar en el accounting_supplier_party si está disponible
        if accounting_supplier_party is not None:
            additional_account_locations = [
                'cbc:AdditionalAccountID',
                './/cbc:AdditionalAccountID'
            ]
            
            if namespaces:
                for location in additional_account_locations:
                    elem = accounting_supplier_party.find(location, namespaces)
                    if elem is not None and elem.text and elem.text.strip():
                        supplier_data['organization_code'] = elem.text.strip()
                        _logger.info(f"Encontrado organization_code en accounting_supplier_party: {supplier_data['organization_code']}")
                        break
            
            # Buscar sin namespaces en accounting_supplier_party
            if not supplier_data.get('organization_code'):
                for elem in accounting_supplier_party.iter():
                    if (elem.tag.endswith('}AdditionalAccountID') or elem.tag == 'AdditionalAccountID') and elem.text and elem.text.strip():
                        supplier_data['organization_code'] = elem.text.strip()
                        _logger.info(f"Encontrado organization_code en accounting_supplier_party (sin ns): {supplier_data['organization_code']}")
                        break
        
        # Si no se encontró en accounting_supplier_party, buscar en supplier_party
        if not supplier_data.get('organization_code'):
            additional_account_locations = [
                './/cbc:AdditionalAccountID',
                '../cbc:AdditionalAccountID',  # Buscar en el elemento padre
                'cbc:AdditionalAccountID'
            ]
            
            if namespaces:
                for location in additional_account_locations:
                    elem = supplier_party.find(location, namespaces)
                    if elem is not None and elem.text and elem.text.strip():
                        supplier_data['organization_code'] = elem.text.strip()
                        _logger.info(f"Encontrado organization_code: {supplier_data['organization_code']}")
                        break
            
            # Buscar sin namespaces para AdditionalAccountID, también en el elemento padre
            if not supplier_data.get('organization_code'):
                # Primero buscar en el elemento actual
                for elem in supplier_party.iter():
                    if (elem.tag.endswith('}AdditionalAccountID') or elem.tag == 'AdditionalAccountID') and elem.text and elem.text.strip():
                        supplier_data['organization_code'] = elem.text.strip()
                        _logger.info(f"Encontrado organization_code (sin ns): {supplier_data['organization_code']}")
                        break
                
                # Si no se encuentra, buscar en el elemento padre
                if not supplier_data.get('organization_code') and supplier_party.getparent() is not None:
                    parent = supplier_party.getparent()
                    for elem in parent.iter():
                        if (elem.tag.endswith('}AdditionalAccountID') or elem.tag == 'AdditionalAccountID') and elem.text and elem.text.strip():
                            supplier_data['organization_code'] = elem.text.strip()
                            _logger.info(f"Encontrado organization_code en padre (sin ns): {supplier_data['organization_code']}")
                            break
        
        _logger.info(f"Datos fiscales extraídos: {supplier_data}")

    def _find_any_name(self, root):
        """Busca cualquier nombre válido en el XML como último recurso"""
        # Buscar RegistrationName en cualquier parte
        for elem in root.iter():
            if (elem.tag.endswith('}RegistrationName') or elem.tag == 'RegistrationName') and elem.text:
                text = elem.text.strip()
                if len(text) > 3 and not text.isdigit():
                    _logger.info(f"Nombre genérico encontrado: {text}")
                    return text
        
        # Buscar Name que no sea número
        for elem in root.iter():
            if (elem.tag.endswith('}Name') or elem.tag == 'Name') and elem.text:
                text = elem.text.strip()
                if len(text) > 5 and not text.isdigit() and ' ' in text:
                    _logger.info(f"Nombre genérico encontrado: {text}")
                    return text
        
        return None

    def _extract_address_data(self, supplier_party, supplier_data, namespaces):
        """Extrae datos de dirección del proveedor"""
        # Buscar información de ubicación
        address = None
        if namespaces:
            address = supplier_party.find('.//cac:PhysicalLocation/cac:Address', namespaces)
        
        if address is None:
            # Buscar sin namespaces
            for elem in supplier_party.iter():
                if elem.tag.endswith('}Address') or elem.tag == 'Address':
                    address = elem
                    break
        
        if address is not None:
            # Extraer campos de dirección de forma robusta
            fields_map = {
                'city': ['CityName'],
                'state_name': ['CountrySubentity'],
                'state_code': ['CountrySubentityCode'],
                'street': ['Line'],
                'country_code': ['IdentificationCode'],
                'country_name': ['Name']
            }
            
            for field_name, tag_names in fields_map.items():
                for tag_name in tag_names:
                    elem = None
                    if namespaces:
                        elem = address.find(f'.//cbc:{tag_name}', namespaces)
                    
                    if elem is None:
                        for e in address.iter():
                            if e.tag.endswith('}' + tag_name) or e.tag == tag_name:
                                elem = e
                                break
                    
                    if elem is not None and elem.text:
                        supplier_data[field_name] = elem.text.strip()
                        break
            
            # Extraer municipality_code del campo ID
            municipality_elem = None
            if namespaces:
                municipality_elem = address.find('cbc:ID', namespaces)
            
            if municipality_elem is None:
                for elem in address.iter():
                    if (elem.tag.endswith('}ID') or elem.tag == 'ID') and elem.text and elem.text.strip():
                        municipality_elem = elem
                        break
            
            if municipality_elem is not None and municipality_elem.text:
                supplier_data['municipality_code'] = municipality_elem.text.strip()

    def _extract_contact_data(self, supplier_party, supplier_data, namespaces):
        """Extrae datos de contacto del proveedor"""
        # Buscar información de contacto
        contact = None
        if namespaces:
            contact = supplier_party.find('cac:Contact', namespaces)
        
        if contact is None:
            for elem in supplier_party.iter():
                if elem.tag.endswith('}Contact') or elem.tag == 'Contact':
                    contact = elem
                    break
        
        if contact is not None:
            # Teléfono
            phone_elem = None
            if namespaces:
                phone_elem = contact.find('cbc:Telephone', namespaces)
            
            if phone_elem is None:
                for elem in contact.iter():
                    if elem.tag.endswith('}Telephone') or elem.tag == 'Telephone':
                        phone_elem = elem
                        break
            
            if phone_elem is not None and phone_elem.text:
                supplier_data['phone'] = phone_elem.text.strip()
            
            # Email
            email_elem = None
            if namespaces:
                email_elem = contact.find('cbc:ElectronicMail', namespaces)
            
            if email_elem is None:
                for elem in contact.iter():
                    if elem.tag.endswith('}ElectronicMail') or elem.tag == 'ElectronicMail':
                        email_elem = elem
                        break
            
            if email_elem is not None and email_elem.text:
                supplier_data['email'] = email_elem.text.strip()

    def _create_or_update_supplier(self, supplier_data):
        """Crea o actualiza el proveedor"""
        # Si no hay nombre, crear uno genérico
        if not supplier_data.get('name'):
            supplier_data['name'] = f"Proveedor Importado {fields.Datetime.now().strftime('%Y%m%d%H%M%S')}"
            _logger.warning(f"No se encontró nombre del proveedor, usando nombre genérico: {supplier_data['name']}")
        
        # Buscar si el proveedor ya existe
        supplier = self.env['res.partner'].search([
            ('name', '=', supplier_data['name']),
            ('is_company', '=', True),
            ('supplier_rank', '>', 0)
        ], limit=1)
        
        # Preparar valores para crear/actualizar
        vals = {
            'name': supplier_data['name'],
            'is_company': True,
            'supplier_rank': 1,
        }
        
        # Agregar información de dirección si está disponible
        if supplier_data.get('street'):
            vals['street'] = supplier_data['street']
        if supplier_data.get('city'):
            vals['city'] = supplier_data['city']
        if supplier_data.get('phone'):
            vals['phone'] = supplier_data['phone']
        if supplier_data.get('email'):
            vals['email'] = supplier_data['email']
        
        # Campos fiscales básicos - Solo usar identification_co_number para Colombia
        if supplier_data.get('identification_co_number'):
            vals['identification_co_number'] = supplier_data['identification_co_number']
        
        # Buscar tipo de documento de identificación
        if supplier_data.get('document_type_code'):
            _logger.info(f"Buscando tipo de documento con código: {supplier_data['document_type_code']}")
            document_type = self.env['l10n_co_fl.type_document_identification'].search([
                ('code', '=', supplier_data['document_type_code'])
            ], limit=1)
            if document_type:
                vals['l10n_co_edi_type_document_identification_id'] = document_type.id
                _logger.info(f"Tipo de documento encontrado: {document_type.name}")
            else:
                _logger.warning(f"Tipo de documento no encontrado para código: {supplier_data['document_type_code']}")
        
        # Buscar tipo de régimen
        if supplier_data.get('regime_code'):
            _logger.info(f"Buscando régimen con código: {supplier_data['regime_code']}")
            regime_type = self.env['l10n_co_fl.type.regime'].search([
                ('code', '=', supplier_data['regime_code'])
            ], limit=1)
            if regime_type:
                vals['type_regime_id'] = regime_type.id
                _logger.info(f"Régimen encontrado: {regime_type.name}")
            else:
                _logger.warning(f"Régimen no encontrado para código: {supplier_data['regime_code']}")
        
        # Buscar tipo de responsabilidad fiscal
        if supplier_data.get('liability_code'):
            _logger.info(f"Buscando responsabilidad con código: {supplier_data['liability_code']}")
            liability_type = self.env['l10n_co_fl.type.liability'].search([
                ('code', '=', supplier_data['liability_code'])
            ], limit=1)
            if liability_type:
                vals['l10n_co_edi_type_liability_id'] = liability_type.id
                _logger.info(f"Responsabilidad encontrada: {liability_type.name}")
            else:
                _logger.warning(f"Responsabilidad no encontrada para código: {supplier_data['liability_code']}")
        
        # Buscar tipo de organización
        if supplier_data.get('organization_code'):
            _logger.info(f"Buscando organización con código: {supplier_data['organization_code']}")
            organization_type = self.env['l10n_co_fl.type.organization'].search([
                ('code', '=', supplier_data['organization_code'])
            ], limit=1)
            if organization_type:
                vals['l10n_co_edi_type_organization_id'] = organization_type.id
                _logger.info(f"Organización encontrada: {organization_type.name}")
            else:
                _logger.warning(f"Organización no encontrada para código: {supplier_data['organization_code']}")
        
        # Buscar municipio
        if supplier_data.get('municipality_code'):
            municipality = self.env['l10n_co_fl.municipality'].search([
                ('code', '=', supplier_data['municipality_code'])
            ], limit=1)
            if municipality:
                vals['municipality_id'] = municipality.id
        
        # Buscar país
        if supplier_data.get('country_code'):
            country = self.env['res.country'].search([
                ('code', '=', supplier_data['country_code'])
            ], limit=1)
            if country:
                vals['country_id'] = country.id
        
        # Buscar estado
        if supplier_data.get('state_code') and vals.get('country_id'):
            state = self.env['res.country.state'].search([
                ('code', '=', supplier_data['state_code']),
                ('country_id', '=', vals['country_id'])
            ], limit=1)
            if state:
                vals['state_id'] = state.id
        
        if supplier:
            # Actualizar proveedor existente
            _logger.info(f"Actualizando proveedor existente: {supplier.name} con valores: {vals}")
            supplier.write(vals)
        else:
            # Crear nuevo proveedor
            _logger.info(f"Creando nuevo proveedor con valores: {vals}")
            supplier = self.env['res.partner'].create(vals)
        
        # Log de verificación de campos fiscales después de crear/actualizar
        _logger.info(f"Proveedor final - identification_co_number: {supplier.identification_co_number}")
        _logger.info(f"Proveedor final - l10n_co_edi_type_document_identification_id: {supplier.l10n_co_edi_type_document_identification_id.name if supplier.l10n_co_edi_type_document_identification_id else 'None'}")
        _logger.info(f"Proveedor final - l10n_co_edi_type_liability_id: {supplier.l10n_co_edi_type_liability_id.name if supplier.l10n_co_edi_type_liability_id else 'None'}")
        _logger.info(f"Proveedor final - type_regime_id: {supplier.type_regime_id.name if supplier.type_regime_id else 'None'}")
        _logger.info(f"Proveedor final - l10n_co_edi_type_organization_id: {supplier.l10n_co_edi_type_organization_id.name if supplier.l10n_co_edi_type_organization_id else 'None'}")
        
        return supplier

    def _extract_invoice_data(self, root, namespaces):
        """Extrae datos de la factura del XML"""
        invoice_data = {}
        
        # Buscar número de factura en múltiples ubicaciones
        invoice_id_locations = [
            './/cbc:ID',
            './cbc:ID'
        ]
        
        if namespaces:
            for location in invoice_id_locations:
                elem = root.find(location, namespaces)
                if elem is not None and elem.text and elem.text.strip():
                    # Evitar IDs de líneas o otros elementos
                    if not elem.text.strip().isdigit() or len(elem.text.strip()) > 3:
                        invoice_data['invoice_number'] = elem.text.strip()
                        _logger.info(f"Número de factura encontrado: {invoice_data['invoice_number']}")
                        break
        
        # Buscar sin namespaces si no se encontró
        if not invoice_data.get('invoice_number'):
            for elem in root.iter():
                if elem.tag.endswith('}ID') or elem.tag == 'ID':
                    if elem.text and elem.text.strip() and len(elem.text.strip()) > 3:
                        # Verificar que sea el ID principal (generalmente el primero)
                        if elem.getparent() == root:
                            invoice_data['invoice_number'] = elem.text.strip()
                            _logger.info(f"Número de factura encontrado sin namespaces: {invoice_data['invoice_number']}")
                            break
        
        # Buscar CUFE con múltiples enfoques
        cufe_locations = [
            './/cbc:UUID[@schemeID="1"][@schemeName="CUFE-SHA384"]',
            './/cbc:UUID[@schemeName="CUFE-SHA384"]',
            './/cbc:UUID'
        ]
        
        if namespaces:
            for location in cufe_locations:
                elem = root.find(location, namespaces)
                if elem is not None and elem.text and elem.text.strip():
                    invoice_data['cufe'] = elem.text.strip()
                    _logger.info(f"CUFE encontrado: {invoice_data['cufe']}")
                    break
        
        # Buscar CUFE sin namespaces
        if not invoice_data.get('cufe'):
            for elem in root.iter():
                if elem.tag.endswith('}UUID') or elem.tag == 'UUID':
                    if elem.text and elem.text.strip() and len(elem.text.strip()) > 10:
                        invoice_data['cufe'] = elem.text.strip()
                        _logger.info(f"CUFE encontrado sin namespaces: {invoice_data['cufe']}")
                        break
        
        return invoice_data

    def _process_invoice_lines(self, root, namespaces):
        """Procesa las líneas de la factura y crea líneas de orden de compra"""
        # Limpiar líneas existentes
        self.order_line.unlink()
        
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
                self._create_purchase_line(product, line_data)

    def _create_generic_line(self):
        """Crea una línea genérica cuando no se encuentran líneas en el XML"""
        # Buscar o crear producto genérico (sin referencia interna para evitar conflictos)
        product_name = 'Producto Importado XML'
        
        product = self.env['product.product'].search([
            ('name', '=', product_name),
            ('default_code', '=', False)  # Sin referencia interna
        ], limit=1)
        
        if not product:
            product_vals = {
                'name': product_name,
                'type': 'consu',  # Crear como consumibles
                'purchase_ok': True,
                # No asignar default_code para evitar conflictos
            }
            
            try:
                product = self.env['product.product'].create(product_vals)
                _logger.info(f"Producto genérico creado: {product.name}")
            except Exception as e:
                _logger.error(f"Error al crear producto genérico: {str(e)}")
                raise UserError(f"Error al crear producto genérico: {str(e)}")
        
        # Crear línea de compra genérica
        line_vals = {
            'order_id': self.id,
            'product_id': product.id,
            'name': product_name,
            'product_qty': 1.0,
            'price_unit': 0.0,
            'date_planned': fields.Datetime.now(),
        }
        
        self.env['purchase.order.line'].create(line_vals)

    def _extract_line_data(self, line, namespaces):
        """Extrae datos de una línea de factura"""
        line_data = {}
        
        # ID de línea
        line_id = self._find_element_text(line, ['cbc:ID', 'ID'], namespaces)
        if line_id:
            line_data['line_id'] = line_id
        
        # Descripción del producto - múltiples ubicaciones
        description_locations = [
            'cbc:Description',
            'cac:Item/cbc:Description', 
            'cac:Item/cbc:Name',
            'Description',
            'Name'
        ]
        description = self._find_element_text(line, description_locations, namespaces)
        if description:
            line_data['description'] = description
        
        # Marca
        brand = self._find_element_text(line, ['cbc:BrandName', 'BrandName'], namespaces)
        if brand:
            line_data['brand'] = brand
        
        # Modelo
        model = self._find_element_text(line, ['cbc:ModelName', 'ModelName'], namespaces)
        if model:
            line_data['model'] = model
        
        # Referencia interna - múltiples ubicaciones
        default_code_locations = [
            './/cac:StandardItemIdentification/cbc:ID[@schemeID="999"]',
            './/cac:StandardItemIdentification/cbc:ID',
            './/cac:Item/cac:StandardItemIdentification/cbc:ID',
            './/cac:SellersItemIdentification/cbc:ID',
            './/cac:BuyersItemIdentification/cbc:ID'
        ]
        
        for location in default_code_locations:
            elem = None
            if namespaces:
                elem = line.find(location, namespaces)
            
            if elem is None and '//' in location:
                # Buscar sin namespaces
                tag = location.split('/')[-1]
                for e in line.iter():
                    if e.tag.endswith('}' + tag) or e.tag == tag:
                        elem = e
                        break
            
            if elem is not None and elem.text and elem.text.strip():
                line_data['default_code'] = elem.text.strip()
                break
        
        # Precio y cantidad
        self._extract_price_and_quantity(line, line_data, namespaces)
        
        # Extraer información de impuestos (DESPUÉS de precio y cantidad para calcular monto gravable)
        self._extract_tax_data(line, line_data, namespaces)
        
        return line_data

    def _find_element_text(self, parent, tag_list, namespaces):
        """Busca el texto de un elemento usando múltiples tags posibles"""
        for tag in tag_list:
            # Buscar con namespaces
            if namespaces and ':' in tag:
                elem = parent.find('.//'+tag, namespaces) or parent.find(tag, namespaces)
                if elem is not None and elem.text and elem.text.strip():
                    return elem.text.strip()
            
            # Buscar sin namespaces
            simple_tag = tag.split(':')[-1]  # Obtener solo el nombre del tag
            for elem in parent.iter():
                if (elem.tag.endswith('}' + simple_tag) or elem.tag == simple_tag) and elem.text and elem.text.strip():
                    return elem.text.strip()
        
        return None

    def _extract_price_and_quantity(self, line, line_data, namespaces):
        """Extrae precio y cantidad de la línea"""
        # Buscar elemento Price
        price_elem = None
        if namespaces:
            price_elem = line.find('cac:Price', namespaces)
        
        if price_elem is None:
            for elem in line.iter():
                if elem.tag.endswith('}Price') or elem.tag == 'Price':
                    price_elem = elem
                    break
        
        if price_elem is not None:
            # Precio unitario
            price_amount = self._find_element_text(price_elem, ['cbc:PriceAmount', 'PriceAmount'], namespaces)
            if price_amount:
                try:
                    line_data['price_unit'] = float(price_amount)
                except ValueError:
                    line_data['price_unit'] = 0.0
            
            # Cantidad
            quantity = self._find_element_text(price_elem, ['cbc:BaseQuantity', 'BaseQuantity'], namespaces)
            if quantity:
                try:
                    line_data['quantity'] = float(quantity)
                except ValueError:
                    line_data['quantity'] = 1.0
            
            # Código de unidad
            if namespaces:
                base_qty_elem = price_elem.find('cbc:BaseQuantity', namespaces)
            else:
                base_qty_elem = None
                for elem in price_elem.iter():
                    if elem.tag.endswith('}BaseQuantity') or elem.tag == 'BaseQuantity':
                        base_qty_elem = elem
                        break
            
            if base_qty_elem is not None:
                unit_code = base_qty_elem.get('unitCode')
                if unit_code:
                    line_data['unit_code'] = unit_code
                    _logger.info(f"Código de unidad extraído de BaseQuantity: {unit_code}")
                
                # Extraer también el nombre de la unidad de medida del XML
                unit_name = base_qty_elem.get('unitCodeListName') or base_qty_elem.get('unitName')
                if unit_name:
                    line_data['unit_name'] = unit_name
                    _logger.info(f"Nombre de unidad extraído: {unit_name}")
        
        # Si no se encontró precio/cantidad, buscar en otros lugares
        if not line_data.get('quantity'):
            # Buscar InvoicedQuantity
            if namespaces:
                invoiced_qty_elem = line.find('cbc:InvoicedQuantity', namespaces)
            else:
                invoiced_qty_elem = None
                for elem in line.iter():
                    if elem.tag.endswith('}InvoicedQuantity') or elem.tag == 'InvoicedQuantity':
                        invoiced_qty_elem = elem
                        break
            
            if invoiced_qty_elem is not None:
                qty_text = invoiced_qty_elem.text
                if qty_text:
                    try:
                        line_data['quantity'] = float(qty_text)
                    except ValueError:
                        line_data['quantity'] = 1.0
                
                # Extraer código de unidad de InvoicedQuantity si no lo tenemos
                if not line_data.get('unit_code'):
                    unit_code = invoiced_qty_elem.get('unitCode')
                    if unit_code:
                        line_data['unit_code'] = unit_code
                        _logger.info(f"Código de unidad extraído de InvoicedQuantity: {unit_code}")
                    
                    # Extraer también el nombre de la unidad
                    unit_name = invoiced_qty_elem.get('unitCodeListName') or invoiced_qty_elem.get('unitName')
                    if unit_name:
                        line_data['unit_name'] = unit_name
                        _logger.info(f"Nombre de unidad extraído de InvoicedQuantity: {unit_name}")
        
        # Valores por defecto
        if not line_data.get('quantity'):
            line_data['quantity'] = 1.0
        if not line_data.get('price_unit'):
            line_data['price_unit'] = 0.0

    def _extract_tax_data(self, line, line_data, namespaces):
        """Extrae información de impuestos de la línea"""
        line_data['taxes'] = []
        
        # Buscar TaxTotal en la línea
        tax_total_elem = None
        if namespaces:
            tax_total_elem = line.find('cac:TaxTotal', namespaces)
        
        if tax_total_elem is None:
            for elem in line.iter():
                if elem.tag.endswith('}TaxTotal') or elem.tag == 'TaxTotal':
                    tax_total_elem = elem
                    break
        
        if tax_total_elem is not None:
            # Buscar TaxSubtotal elements
            tax_subtotals = []
            if namespaces:
                tax_subtotals = tax_total_elem.findall('cac:TaxSubtotal', namespaces)
            else:
                for elem in tax_total_elem.iter():
                    if elem.tag.endswith('}TaxSubtotal') or elem.tag == 'TaxSubtotal':
                        tax_subtotals.append(elem)
            
            _logger.info(f"TaxSubtotals encontrados: {len(tax_subtotals)}")
            
            for subtotal in tax_subtotals:
                tax_info = self._extract_single_tax(subtotal, namespaces)
                if tax_info:
                    line_data['taxes'].append(tax_info)
                    _logger.info(f"Impuesto extraído - Código: {tax_info.get('tax_code')}, Nombre: {tax_info.get('tax_name')}, Porcentaje: {tax_info.get('percent')}%")
        
        # Si no se encontraron impuestos, agregar IVA excluido del 0%
        if not line_data['taxes']:
            _logger.info("No se encontraron impuestos en la línea, aplicando IVA excluido del 0%")
            line_data['taxes'] = [{
                'tax_code': '01',  # Código DIAN para IVA
                'tax_name': 'IVA',
                'percent': 0.0,
                'taxable_amount': line_data.get('price_unit', 0.0) * line_data.get('quantity', 1.0),
                'tax_amount': 0.0
            }]

    def _extract_single_tax(self, tax_elem, namespaces):
        """Extrae información de un solo impuesto"""
        tax_info = {}
        
        # Monto gravable
        taxable_amount = self._find_element_text(tax_elem, ['cbc:TaxableAmount', 'TaxableAmount'], namespaces)
        if taxable_amount:
            try:
                tax_info['taxable_amount'] = float(taxable_amount)
            except ValueError:
                tax_info['taxable_amount'] = 0.0
        
        # Monto del impuesto
        tax_amount = self._find_element_text(tax_elem, ['cbc:TaxAmount', 'TaxAmount'], namespaces)
        if tax_amount:
            try:
                tax_info['tax_amount'] = float(tax_amount)
            except ValueError:
                tax_info['tax_amount'] = 0.0
        
        # Buscar TaxCategory para obtener información del esquema de impuesto
        tax_category = None
        if namespaces:
            tax_category = tax_elem.find('cac:TaxCategory', namespaces)
        else:
            for elem in tax_elem.iter():
                if elem.tag.endswith('}TaxCategory') or elem.tag == 'TaxCategory':
                    tax_category = elem
                    break
        
        if tax_category is not None:
            # Porcentaje del impuesto - CRÍTICO para obtener el porcentaje correcto
            percent_text = self._find_element_text(tax_category, ['cbc:Percent', 'Percent'], namespaces)
            if percent_text:
                try:
                    tax_info['percent'] = float(percent_text)
                    _logger.info(f"Porcentaje extraído correctamente: {tax_info['percent']}%")
                except ValueError:
                    tax_info['percent'] = 0.0
                    _logger.warning(f"Error al convertir porcentaje: {percent_text}")
            else:
                # Si no hay porcentaje explícito, intentar calcularlo a partir de los montos
                if tax_info.get('tax_amount', 0) > 0 and tax_info.get('taxable_amount', 0) > 0:
                    calculated_percent = (tax_info['tax_amount'] / tax_info['taxable_amount']) * 100
                    tax_info['percent'] = round(calculated_percent, 2)
                    _logger.info(f"Porcentaje calculado a partir de montos: {tax_info['percent']}%")
                else:
                    tax_info['percent'] = 0.0
                    _logger.info("No se encontró porcentaje ni se pudo calcular, usando 0%")
            
            # Buscar TaxScheme
            tax_scheme = None
            if namespaces:
                tax_scheme = tax_category.find('cac:TaxScheme', namespaces)
            else:
                for elem in tax_category.iter():
                    if elem.tag.endswith('}TaxScheme') or elem.tag == 'TaxScheme':
                        tax_scheme = elem
                        break
            
            if tax_scheme is not None:
                # ID del tipo de impuesto (código DIAN)
                tax_id = self._find_element_text(tax_scheme, ['cbc:ID', 'ID'], namespaces)
                if tax_id:
                    tax_info['tax_code'] = tax_id
                
                # Nombre del tipo de impuesto
                tax_name = self._find_element_text(tax_scheme, ['cbc:Name', 'Name'], namespaces)
                if tax_name:
                    tax_info['tax_name'] = tax_name
        
        # Validar que tenemos la información mínima necesaria
        if tax_info.get('tax_code') and 'percent' in tax_info:
            _logger.info(f"Impuesto completo extraído: Código={tax_info['tax_code']}, Nombre={tax_info.get('tax_name')}, Porcentaje={tax_info['percent']}%")
            return tax_info
        else:
            _logger.warning(f"Información de impuesto incompleta: {tax_info}")
            return None

    def _create_or_update_product(self, line_data):
        """Crea o actualiza el producto - NUNCA crear duplicados por referencia interna"""
        product = None
        
        # Primero: Buscar producto por referencia interna si existe
        if line_data.get('default_code'):
            product = self.env['product.product'].search([
                ('default_code', '=', line_data['default_code'])
            ], limit=1)
            
            if product:
                _logger.info(f"Producto encontrado por referencia interna '{line_data['default_code']}': {product.name}")
                # Si encontramos por referencia interna, usar ese producto y NO crear uno nuevo
                # Solo actualizar campos seguros (nombre/descripción)
                update_vals = {}
                
                if line_data.get('description') and line_data['description'] != product.name:
                    update_vals['name'] = line_data['description']
                
                # Solo actualizar UOM si no está configurada o es diferente
                if line_data.get('unit_code'):
                    unit_name = line_data.get('unit_name')
                    uom = self._find_uom_by_dian_code(line_data['unit_code'], unit_name)
                    if uom and (not product.uom_id or product.uom_id.id != uom.id):
                        try:
                            update_vals['uom_id'] = uom.id
                            update_vals['uom_po_id'] = uom.id
                        except Exception as e:
                            _logger.warning(f"No se pudo actualizar UOM del producto {product.name}: {str(e)}")
                
                # Aplicar actualizaciones solo si hay cambios
                if update_vals:
                    try:
                        product.write(update_vals)
                        _logger.info(f"Producto actualizado: {product.name} (ref: {product.default_code})")
                    except Exception as e:
                        _logger.warning(f"No se pudo actualizar el producto {product.name}: {str(e)}")
                
                return product
        
        # Segundo: Si no hay referencia interna o no se encontró por referencia, buscar por nombre
        if not product and line_data.get('description'):
            product = self.env['product.product'].search([
                ('name', '=', line_data['description'])
            ], limit=1)
            
            if product:
                _logger.info(f"Producto encontrado por nombre '{line_data['description']}': {product.name}")
                # Solo actualizar campos seguros
                update_vals = {}
                
                # CRÍTICO: NO actualizar referencia interna si ya existe otro producto con esa referencia
                if line_data.get('default_code') and line_data['default_code'] != product.default_code:
                    # Verificar que no exista otro producto con esa referencia
                    existing_with_code = self.env['product.product'].search([
                        ('default_code', '=', line_data['default_code']),
                        ('id', '!=', product.id)
                    ], limit=1)
                    
                    if existing_with_code:
                        _logger.warning(f"No se puede asignar referencia '{line_data['default_code']}' al producto '{product.name}' porque ya existe en '{existing_with_code.name}'")
                    else:
                        update_vals['default_code'] = line_data['default_code']
                
                # Actualizar UOM si es necesario
                if line_data.get('unit_code'):
                    unit_name = line_data.get('unit_name')
                    uom = self._find_uom_by_dian_code(line_data['unit_code'], unit_name)
                    if uom and (not product.uom_id or product.uom_id.id != uom.id):
                        try:
                            update_vals['uom_id'] = uom.id
                            update_vals['uom_po_id'] = uom.id
                        except Exception as e:
                            _logger.warning(f"No se pudo actualizar UOM del producto {product.name}: {str(e)}")
                
                # Aplicar actualizaciones
                if update_vals:
                    try:
                        product.write(update_vals)
                        _logger.info(f"Producto actualizado: {product.name} (ref: {product.default_code or 'Sin ref'})")
                    except Exception as e:
                        _logger.warning(f"No se pudo actualizar el producto {product.name}: {str(e)}")
                
                return product
        
        # Tercero: Crear nuevo producto solo si no existe
        # VERIFICACIÓN FINAL: Asegurar que no existe un producto con la misma referencia
        if line_data.get('default_code'):
            existing_product = self.env['product.product'].search([
                ('default_code', '=', line_data['default_code'])
            ], limit=1)
            
            if existing_product:
                _logger.warning(f"PREVENCIÓN DE DUPLICADO: Ya existe un producto con referencia '{line_data['default_code']}': {existing_product.name}. Usando el existente.")
                return existing_product
        
        # Preparar valores para nuevo producto
        vals = {
            'name': line_data.get('description', 'Producto importado'),
            'type': 'consu',  # Siempre crear como consumibles
            'purchase_ok': True,
        }
        
        if line_data.get('default_code'):
            vals['default_code'] = line_data['default_code']
        
        # Buscar unidad de medida si está especificada
        if line_data.get('unit_code'):
            unit_name = line_data.get('unit_name')
            uom = self._find_uom_by_dian_code(line_data['unit_code'], unit_name)
            if uom:
                vals['uom_id'] = uom.id
                vals['uom_po_id'] = uom.id
        
        # Crear nuevo producto
        try:
            product = self.env['product.product'].create(vals)
            _logger.info(f"Nuevo producto creado: {product.name} (ref: {product.default_code or 'Sin ref'})")
        except Exception as e:
            _logger.error(f"Error al crear producto: {str(e)}")
            raise UserError(f"Error al crear el producto: {str(e)}")
        
        return product

    def _create_purchase_line(self, product, line_data):
        """Crea una línea de orden de compra"""
        vals = {
            'order_id': self.id,
            'product_id': product.id,
            'name': line_data.get('description', product.name),
            'product_qty': line_data.get('quantity', 1.0),
            'price_unit': line_data.get('price_unit', 0.0),
            'date_planned': fields.Datetime.now(),
        }
        
        # Buscar unidad de medida
        if line_data.get('unit_code'):
            unit_name = line_data.get('unit_name')
            uom = self._find_uom_by_dian_code(line_data['unit_code'], unit_name)
            if uom:
                vals['product_uom'] = uom.id
        
        # Procesar impuestos - SIEMPRE debe haber al menos un impuesto
        tax_ids = []
        
        if line_data.get('taxes'):
            for tax_info in line_data['taxes']:
                if tax_info.get('tax_code'):
                    # Usar 'percent' en lugar de 'tax_percent'
                    tax_percent = tax_info.get('percent', 0.0)
                    tax = self._find_tax_by_dian_code(
                        tax_info['tax_code'],
                        tax_info.get('tax_name'),
                        tax_percent
                    )
                    if tax:
                        tax_ids.append(tax.id)
                        _logger.info(f"Impuesto {tax.name} ({tax.amount}%) aplicado a la línea")
        
        # Si no se aplicó ningún impuesto, aplicar IVA excluido del 0%
        if not tax_ids:
            _logger.info("No se aplicaron impuestos, buscando o creando IVA 0%")
            default_tax = self._find_tax_by_dian_code('01', 'IVA', 0.0)
            if default_tax:
                tax_ids.append(default_tax.id)
                _logger.info(f"IVA excluido del 0% aplicado: {default_tax.name}")
        
        if tax_ids:
            vals['taxes_id'] = [(6, 0, tax_ids)]
            _logger.info(f"Total de impuestos aplicados: {len(tax_ids)}")
        
        purchase_line = self.env['purchase.order.line'].create(vals)
        _logger.info(f"Línea de compra creada: {purchase_line.name} con {len(tax_ids)} impuesto(s)")
        return purchase_line

    def _find_uom_by_dian_code(self, dian_code, unit_name=None):
        """Busca unidad de medida por código DIAN usando l10n_co_catalog"""
        # Buscar en l10n_co_fl.unit.measure por código DIAN
        dian_unit = self.env['l10n_co_fl.unit.measure'].search([
            ('code', '=', dian_code)
        ], limit=1)
        
        if dian_unit:
            # Buscar UOM que tenga este edi_unit_measure_id
            uom = self.env['uom.uom'].search([
                ('edi_unit_measure_id', '=', dian_unit.id)
            ], limit=1)
            
            if uom:
                return uom
            else:
                # No existe UOM con este edi_unit_measure_id, crear una nueva
                _logger.info(f"Creando nueva UOM para código DIAN {dian_code} con nombre {dian_unit.name}")
                
                # Determinar categoría de UOM (usar la categoría "Unit" por defecto)
                uom_category = self.env.ref('uom.product_uom_categ_unit', raise_if_not_found=False)
                if not uom_category:
                    # Si no existe la categoría Unit, buscar la primera disponible
                    uom_category = self.env['uom.category'].search([], limit=1)
                
                # Usar el nombre del XML si está disponible, sino el de la tabla DIAN
                display_name = unit_name or dian_unit.name
                
                try:
                    new_uom = self.env['uom.uom'].create({
                        'name': display_name,
                        'category_id': uom_category.id,
                        'uom_type': 'reference',
                        'factor': 1.0,
                        'rounding': 0.001,
                        'edi_unit_measure_id': dian_unit.id,
                    })
                    _logger.info(f"UOM creada exitosamente: {new_uom.name} con edi_unit_measure_id: {dian_unit.id}")
                    return new_uom
                except Exception as e:
                    _logger.error(f"Error creando UOM para código {dian_code}: {str(e)}")
                    # En caso de error, continuar con el mapeo común
        
        # Si no se encuentra en DIAN, usar mapeo común como fallback
        uom_mapping = {
            'NIU': 'Units',     # Unidad
            'KGM': 'kg',        # Kilogramo
            'LTR': 'L',         # Litro
            'MTR': 'm',         # Metro
            'MTK': 'm²',        # Metro cuadrado
            'MTQ': 'm³',        # Metro cúbico
            'HUR': 'Hour(s)',   # Hora
            'DAY': 'Day(s)',    # Día
            'TNE': 't',         # Tonelada
            'GRM': 'g',         # Gramo
        }
        
        unit_name_mapped = uom_mapping.get(dian_code)
        if unit_name_mapped:
            uom = self.env['uom.uom'].search([
                ('name', '=', unit_name_mapped)
            ], limit=1)
            if uom:
                return uom
        
        # Como último recurso, usar unidad por defecto
        return self.env.ref('uom.product_uom_unit', raise_if_not_found=False)

    def _find_tax_by_dian_code(self, dian_code, tax_name=None, tax_percent=0.0):
        """Busca impuesto por código DIAN y porcentaje, priorizando impuestos existentes"""
        _logger.info(f"Buscando impuesto DIAN con código: {dian_code}, nombre: {tax_name}, porcentaje: {tax_percent}")
        
        # Buscar en l10n_co_fl.tax por código DIAN
        dian_tax = self.env['l10n_co_fl.tax'].search([
            ('code', '=', dian_code)
        ], limit=1)
        
        if dian_tax:
            _logger.info(f"Código DIAN encontrado: {dian_tax.name} ({dian_tax.code})")
            
            # PRIORIDAD 1: Buscar impuesto que coincida exactamente con edi_tax_id y amount
            # SIN importar el nombre - esto es lo más importante
            tax = self.env['account.tax'].search([
                ('edi_tax_id', '=', dian_tax.id),
                ('amount', '=', tax_percent),
                ('type_tax_use', '=', 'purchase')
            ], limit=1)
            
            if tax:
                _logger.info(f"Impuesto existente encontrado por edi_tax_id y amount: {tax.name} (edi_tax_id: {dian_tax.id}, amount: {tax.amount}%)")
                return tax
            
            # PRIORIDAD 2: Buscar cualquier impuesto con el mismo edi_tax_id, sin importar el porcentaje
            # Esto es útil cuando hay pequeñas diferencias de redondeo
            existing_taxes = self.env['account.tax'].search([
                ('edi_tax_id', '=', dian_tax.id),
                ('type_tax_use', '=', 'purchase')
            ])
            
            if existing_taxes:
                # Buscar el que tenga el porcentaje más cercano
                closest_tax = None
                min_difference = float('inf')
                
                for existing_tax in existing_taxes:
                    difference = abs(existing_tax.amount - tax_percent)
                    if difference < min_difference:
                        min_difference = difference
                        closest_tax = existing_tax
                
                # Si la diferencia es menor a 0.1%, usar el impuesto existente
                if closest_tax and min_difference <= 0.1:
                    _logger.info(f"Impuesto existente encontrado con porcentaje cercano: {closest_tax.name} (diferencia: {min_difference}%)")
                    return closest_tax
            
            # PRIORIDAD 3: Solo crear nuevo impuesto si no existe ninguno con el edi_tax_id
            _logger.info(f"No se encontró impuesto existente. Creando nuevo impuesto con código: {dian_code}, porcentaje: {tax_percent}%")
            
            # Preparar nombre esperado
            expected_name = tax_name if tax_name else dian_tax.name
            if tax_percent > 0:
                expected_name = f"{expected_name} ({tax_percent}%)"
            
            # Buscar el tax_group_id más apropiado
            tax_group = self._find_best_tax_group(tax_name, tax_percent, dian_code)
            
            # Preparar valores del impuesto
            tax_vals = {
                'name': expected_name,
                'description': f"Impuesto {expected_name} - Código DIAN: {dian_code}",
                'amount': tax_percent,
                'amount_type': 'percent',
                'type_tax_use': 'purchase',
                'edi_tax_id': dian_tax.id,
                'active': True,
            }
            
            if tax_group:
                tax_vals['tax_group_id'] = tax_group.id
                _logger.info(f"Tax group asignado: {tax_group.name}")
            
            try:
                tax = self.env['account.tax'].create(tax_vals)
                _logger.info(f"Nuevo impuesto creado: {tax.name} (ID: {tax.id}, edi_tax_id: {dian_tax.id}, amount: {tax.amount}%, tax_group: {tax_group.name if tax_group else 'No asignado'})")
                return tax
            except Exception as e:
                _logger.error(f"Error al crear impuesto: {e}")
                return None
        
        # Si no se encuentra en DIAN, buscar impuestos genéricos existentes
        if tax_name and tax_percent >= 0:
            _logger.warning(f"Código DIAN {dian_code} no encontrado en l10n_co_fl.tax. Buscando impuestos existentes.")
            
            # PRIORIDAD 1: Buscar impuesto existente con el mismo porcentaje exacto
            existing_tax = self.env['account.tax'].search([
                ('amount', '=', tax_percent),
                ('type_tax_use', '=', 'purchase'),
                ('active', '=', True)
            ], limit=1)
            
            if existing_tax:
                _logger.info(f"Impuesto existente encontrado por porcentaje: {existing_tax.name} ({existing_tax.amount}%)")
                return existing_tax
            
            # PRIORIDAD 2: Buscar impuesto con nombre similar
            if tax_name:
                existing_tax = self.env['account.tax'].search([
                    ('name', 'ilike', tax_name),
                    ('amount', '=', tax_percent),
                    ('type_tax_use', '=', 'purchase'),
                    ('active', '=', True)
                ], limit=1)
                
                if existing_tax:
                    _logger.info(f"Impuesto existente encontrado por nombre y porcentaje: {existing_tax.name}")
                    return existing_tax
            
            # PRIORIDAD 3: Buscar impuesto con porcentaje cercano (diferencia <= 0.5%)
            similar_taxes = self.env['account.tax'].search([
                ('type_tax_use', '=', 'purchase'),
                ('active', '=', True)
            ])
            
            closest_tax = None
            min_difference = float('inf')
            
            for existing_tax in similar_taxes:
                difference = abs(existing_tax.amount - tax_percent)
                if difference <= 0.5 and difference < min_difference:
                    min_difference = difference
                    closest_tax = existing_tax
            
            if closest_tax:
                _logger.info(f"Impuesto existente con porcentaje cercano encontrado: {closest_tax.name} (diferencia: {min_difference}%)")
                return closest_tax
            
            # ÚLTIMO RECURSO: Crear impuesto genérico solo si no existe ninguno similar
            _logger.info(f"No se encontró impuesto similar. Creando impuesto genérico como último recurso.")
            
            # Buscar el tax_group_id más apropiado
            tax_group = self._find_best_tax_group(tax_name, tax_percent, dian_code)
            
            # Crear impuesto genérico
            generic_name = f"{tax_name} ({tax_percent}%)" if tax_percent > 0 else tax_name
            tax_vals = {
                'name': generic_name,
                'description': f"Impuesto importado de XML - {tax_name} al {tax_percent}%",
                'amount': tax_percent,
                'amount_type': 'percent',
                'type_tax_use': 'purchase',
                'active': True,
            }
            
            if tax_group:
                tax_vals['tax_group_id'] = tax_group.id
                _logger.info(f"Tax group asignado a impuesto genérico: {tax_group.name}")
            
            try:
                tax = self.env['account.tax'].create(tax_vals)
                _logger.info(f"Impuesto genérico creado como último recurso: {tax.name} (amount: {tax.amount}%, tax_group: {tax_group.name if tax_group else 'No asignado'})")
                return tax
            except Exception as e:
                _logger.error(f"Error al crear impuesto genérico: {e}")
                return None

        # Como último recurso, retornar None si no se puede crear el impuesto
        _logger.warning(f"No se pudo encontrar o crear impuesto para código: {dian_code}")
        return None

    def _find_best_tax_group(self, tax_name, tax_percent, dian_code):
        """Busca el mejor tax_group_id basado en el nombre y porcentaje del impuesto"""
        
        # Mapeo de códigos DIAN a tipos de impuestos
        dian_to_tax_type = {
            '01': 'IVA',      # IVA
            '02': 'INC',      # Impuesto Nacional al Consumo
            '03': 'ICA',      # Impuesto de Industria y Comercio
            '04': 'CREE',     # CREE
            '05': 'R REN',    # Retención en la fuente
            '06': 'R IVA',    # Retención de IVA
            '07': 'R ICA',    # Retención de ICA
        }
        
        # Determinar tipo base de impuesto
        base_tax_type = tax_name if tax_name else dian_to_tax_type.get(dian_code, 'IVA')
        
        # Lógica de búsqueda del tax group más apropiado
        search_patterns = []
        
        if 'IVA' in base_tax_type.upper():
            # Para IVA, buscar por porcentaje exacto
            if tax_percent == 0:
                search_patterns.append('IVA 0%')
            elif tax_percent == 19:
                search_patterns.append('IVA 19%')
            elif tax_percent == 5:
                search_patterns.append('IVA 5%')
            elif tax_percent == 16:
                search_patterns.append('IVA 16%')
            elif tax_percent == 8:
                search_patterns.append('IVA 8%')
            elif tax_percent == 4:
                search_patterns.append('IVA 4%')
            elif tax_percent == 2.4:
                search_patterns.append('IVA 2.4%')
            elif tax_percent == 2:
                search_patterns.append('IVA 2%')
            elif tax_percent == 0.75:
                search_patterns.append('IVA 0.75%')
            else:
                # Para otros porcentajes, buscar el más cercano
                search_patterns.extend(['IVA 19%', 'IVA 0%'])
        
        elif 'INC' in base_tax_type.upper() or 'CONSUMO' in base_tax_type.upper():
            # Para Impuesto Nacional al Consumo
            if tax_percent == 4:
                search_patterns.append('INC 4%')
            elif tax_percent == 8:
                search_patterns.append('INC 8%')
            elif tax_percent == 16:
                search_patterns.append('INC 16%')
            else:
                search_patterns.extend(['INC 8%', 'INC 4%'])
        
        elif 'CREE' in base_tax_type.upper():
            # Para CREE
            if tax_percent == 4:
                search_patterns.append('CREE 4%')
            elif tax_percent == 8:
                search_patterns.append('CREE 8%')
            elif tax_percent == 16:
                search_patterns.append('CREE 16%')
            else:
                search_patterns.extend(['CREE 8%', 'CREE 4%'])
        
        elif 'RETEFU' in base_tax_type.upper() or 'RENTA' in base_tax_type.upper() or dian_code == '05':
            # Para Retención en la fuente
            renta_percentages = [0, 0.1, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 6, 7, 10, 11, 20, 33]
            closest_percent = min(renta_percentages, key=lambda x: abs(x - tax_percent))
            if closest_percent == 0:
                search_patterns.append('R REN 0%')
            else:
                search_patterns.append(f'R REN {closest_percent}%')
        
        elif 'RETEIVA' in base_tax_type.upper() or dian_code == '06':
            # Para Retención de IVA
            riva_percentages = [0.75, 2.4, 2.85, 16]
            closest_percent = min(riva_percentages, key=lambda x: abs(x - tax_percent))
            search_patterns.append(f'R IVA {closest_percent}%')
        
        elif 'RETEICA' in base_tax_type.upper() or 'ICA' in base_tax_type.upper():
            if dian_code == '07' or 'RETE' in base_tax_type.upper():
                # Para Retención de ICA
                rica_percentages = [0, 0.414, 0.69, 0.966, 1.104, 1.38]
                closest_percent = min(rica_percentages, key=lambda x: abs(x - tax_percent))
                if closest_percent == 0:
                    search_patterns.append('R ICA 0%')
                else:
                    search_patterns.append(f'R ICA {closest_percent}%')
            else:
                # ICA normal (aunque no es común en facturas)
                search_patterns.extend(['IC', 'ICA'])
        
        else:
            # Fallback: buscar por tipo de impuesto común
            search_patterns.extend(['IVA 19%', 'IVA 0%'])
        
        # Buscar el tax group en Odoo
        for pattern in search_patterns:
            tax_group = self.env['account.tax.group'].search([
                ('name', '=', pattern),
                ('country_id.code', '=', 'CO')  # Solo Colombia
            ], limit=1)
            
            if tax_group:
                _logger.info(f"Tax group encontrado: {tax_group.name} para impuesto {base_tax_type} {tax_percent}%")
                return tax_group
        
        # Si no encuentra uno específico, buscar uno genérico
        generic_patterns = ['IVA 0%', 'IVA 19%']
        for pattern in generic_patterns:
            tax_group = self.env['account.tax.group'].search([
                ('name', '=', pattern),
                ('country_id.code', '=', 'CO')
            ], limit=1)
            
            if tax_group:
                _logger.warning(f"Usando tax group genérico: {tax_group.name} para impuesto {base_tax_type} {tax_percent}%")
                return tax_group
        
        _logger.warning(f"No se pudo encontrar tax group apropiado para {base_tax_type} {tax_percent}%")
        return None
        if tax_percent > 0 or tax_name:
            display_name = tax_name if tax_name else f"Impuesto {dian_code}"
            amount = tax_percent if tax_percent > 0 else 0.0
            
            tax_vals = {
                'name': f"{display_name} ({amount}%)" if amount > 0 else display_name,
                'description': f"Impuesto importado del XML - Código: {dian_code}",
                'amount': amount,
                'amount_type': 'percent',
                'type_tax_use': 'purchase',
                'active': True,
            }
            
            try:
                tax = self.env['account.tax'].create(tax_vals)
                _logger.info(f"Impuesto genérico creado: {tax.name}")
                return tax
            except Exception as e:
                _logger.error(f"Error al crear impuesto genérico: {e}")
        
        _logger.warning(f"No se pudo encontrar o crear impuesto para código: {dian_code}")
        return None

    def action_create_invoice(self):
        """Sobrescribir para transferir CUFE a la factura"""
        result = super().action_create_invoice()
        
        # Si hay un CUFE del XML, transferirlo a la factura
        if self.cufe_xml and result and isinstance(result, dict) and result.get('res_id'):
            invoice = self.env['account.move'].browse(result['res_id'])
            if invoice and hasattr(invoice, 'ei_uuid'):
                invoice.write({'ei_uuid': self.cufe_xml})
                _logger.info(f"CUFE transferido a la factura: {self.cufe_xml}")
        
        return result

    def _prepare_invoice(self):
        """Sobrescribir para incluir CUFE en la preparación de la factura"""
        invoice_vals = super()._prepare_invoice()
        
        # Agregar CUFE si existe
        if self.cufe_xml and 'ei_uuid' in self.env['account.move']._fields:
            invoice_vals['ei_uuid'] = self.cufe_xml
            _logger.info(f"CUFE preparado para la factura: {self.cufe_xml}")
        
        return invoice_vals
