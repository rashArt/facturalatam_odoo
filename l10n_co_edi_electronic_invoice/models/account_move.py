from odoo import models, fields, api, _
import json
import re
import requests
from num2words import num2words
import math
import logging
import base64
from io import BytesIO
import qrcode
from urllib.parse import urljoin
import pytz
from datetime import datetime, timedelta
from odoo.exceptions import UserError
import time
_logger = logging.getLogger(__name__)
import zipfile
import io

class AccountMove(models.Model):
    _inherit = 'account.move'


    def _default_payment_method_id(self):
        if not self.env['l10n_co_fl.payment.method'].search_count([]):
            self.env['res.company'].init_csv_data('l10n_co_catalog.l10n_co_fl.payment_method')
        return 1

    is_electronic_invoice = fields.Boolean(string='¿Es una factura electrónica?', related="journal_id.is_electronic_invoice", copy=False)
    number_formatted = fields.Char(string="Número formateado", compute="compute_number_formatted", store=True,copy=False)
    ei_number = fields.Char(string="Edi number", compute="compute_number_formatted", store=True, copy=False,readonly=True)
    resolution_name = fields.Char(related='journal_id.resolution', string='Resolución', copy=False)
    ei_status = fields.Selection([('draft', 'Por Enviar'), ('sent', 'Enviado'), ('accepted', 'Aceptado'), ('rejected', 'Rechazado')], string='Estado de Factura Electrónica', default='draft', copy=False)
    ei_is_valid = fields.Boolean(string='¿Factura Electrónica Válida?', default=False, copy=False)
    ei_message = fields.Text(string='Mensaje de la DIAN',copy=False)
    ei_xml_response = fields.Text(string='Respuesta XML de la DIAN', copy=False)
    ei_zipinvoicexml = fields.Binary(string='Zip de la Factura Electrónica', copy=False)
    ei_zipinvoicexml_filename = fields.Char(string='Nombre del Zip de la Factura Electrónica', copy=False)
    ei_type_document_id = fields.Many2one(related='journal_id.resolution_type_document_id', string='Tipo de Documento',copy=False)
    ei_type_document = fields.Selection(selection=[
        ('none', 'None'),
        ('invoice', 'Factura'),
        ('credit_note', 'Nota de crédito'),
        ('debit_note', 'Nota de débito'),
        ('doc_support', 'Documento Soporte'),
        ('note_support', 'Nota Soporte'),
        ('payroll', 'Nomina'),
        ('payroll_adjustment', 'Nomina Ajuste'),
        ('export_invoice', 'Factura de exportación'),
    ], string="Document type", copy=False, compute='_compute_ei_type_document')
    request_edi = fields.Many2one('co.request.edi',  string='Solicitudes EDI',copy=False)
    is_out_country = fields.Boolean(string='¿Es una factura de exportación?', related="journal_id.is_out_country",copy=False)
    ei_is_correction_without_reference = fields.Boolean(string='¿Es una corrección sin referencia?', default=False, readonly=True)


    # Total taxes only / without withholdings
    ei_amount_tax_withholding = fields.Monetary("Retenciones", compute="_compute_amount", store=True)
    ei_amount_tax_withholding_company = fields.Monetary("Retenciones en moneda de la empresa", compute="_compute_amount",store=True, currency_field='company_currency_id')
    ei_amount_tax_no_withholding = fields.Monetary("Impuestos sin retenciones", compute="_compute_amount", store=True)
    ei_amount_tax_no_withholding_company = fields.Monetary("Impuestos sin retenciones en Moneda de la Empresa",compute="_compute_amount", store=True,currency_field='company_currency_id')
    ei_amount_total_no_withholding = fields.Monetary("Total sin retenciones", compute="_compute_amount",store=True)
    ei_amount_total_no_withholding_company = fields.Monetary("Total sin retenciones en Moneda de la Sociedad",compute="_compute_amount", store=True,currency_field='company_currency_id')

    # Total base excluding tax
    ei_amount_excluded = fields.Monetary("Excluido", compute="_compute_amount", store=True)
    ei_amount_excluded_company = fields.Monetary("Excluido en moneda de la empresa", compute="_compute_amount", store=True,currency_field='company_currency_id')

    # Commercial sample
    ei_amount_commercial_sample = fields.Monetary("Muestra comercial total", compute="_compute_amount", store=True)
    ei_amount_commercial_sample_company = fields.Monetary("Muestra comercial total en moneda de la empresa",compute="_compute_amount", store=True,currency_field='company_currency_id')

    value_letters = fields.Char("Valor en letras", compute="_compute_amount", store=True)
    # ei_is_correction_without_reference = fields.Boolean("¿Es una corrección sin referencia?", default=False,readonly=True)


    payment_form_id = fields.Many2one('l10n_co_fl.payment.form', string='Forma de Pago', copy=True,  compute="_compute_payment_form_id",
                                      readonly=True, ondelete='RESTRICT')
    payment_method_id = fields.Many2one('l10n_co_fl.payment.method', string='Método de pago', default=lambda self: self._default_payment_method_id(), copy=True, ondelete='RESTRICT')


    ei_correction_concept_credit_id = fields.Many2one('l10n_co_fl.credit_note.discrepancy', string='Motivo Credito', copy=False)
    ei_correction_concept_debit_id = fields.Many2one('l10n_co_fl.debit_note.discrepancy', string='Motivo Débito', copy=False)
    ei_detailed_message = fields.Text(string='Mensaje detallado', copy=False)
    status_code = fields.Char(string='Código de estado', copy=False)
    # Order Reference
    order_ref_number = fields.Char(string="Order reference", default=None, copy=False, readonly=True)
    order_ref_date = fields.Date(string="Order date", default=None, copy=False, readonly=True)
    ei_uuid = fields.Char(string="UUID", copy=False)
    manual_ei_uuid = fields.Boolean(string="UUID manual", default=False, copy=False)
    l10n_co_edi_discount_global = fields.Float(
        compute='get_discount_global',
        string='Descuento Global',
        store=True
    )
    ei_qr_data = fields.Text(string="QR data", copy=False, readonly=True)
    ei_qr_image = fields.Binary(string='Código QR', copy=False)
    ei_type_event = fields.Selection([
        ('1', 'Acuse de recibo de Factura Electrónica de Venta - 030'),
        ('2', 'Reclamo de la Factura Electrónica de Venta - 031'),
        ('3', 'Recibo del bien y/o prestación del servicio - 032'),
        ('4', 'Aceptación expresa - 033'),
        ('5', 'Aceptación Tácita - 034'),
        ('6', 'Documento validado por la DIAN - 02'),
        ('7', 'Documento rechazado por la DIAN - 04')
    ], string="Evento")
    ei_type_rejection = fields.Selection([
        ('1', 'Documento con inconsistencias'),
        ('2', 'Mercancía no entregada'),
        ('3', 'Mercancía  entregada parcialmente'),
        ('4', 'Servicio no prestado')
    ], string="Tipo de Rechazo")
    ei_url_pdf = fields.Char(string='URL PDF', copy=False, readonly=True)
    ei_pdf_filename = fields.Char(string='Name PDF', copy=False, readonly=True)
    ei_pdf_binary = fields.Binary(string='Archivo PDF', copy=False)

    ei_period_start_date = fields.Date(string="Fecha de inicio", help="Fecha de inicio del periodo relacionado con la Nota de Credito sin referencia")
    ei_period_end_date = fields.Date(string="Fecha de fin", help="Fecha de fin del periodo relacionado con la Nota de Credito sin referencia")

    # Export Invoice fields
    export_responsible_incharge = fields.Char(string="Responsable a Cargo", help="Responsable a cargo del envío")
    export_departure_place = fields.Char(string="Lugar de Salida", help="Ciudad o lugar de salida de la mercancía")
    export_conveyance = fields.Char(string="Medio de Transporte", help="Medio de transporte utilizado para la exportación")
    export_transport_document_type = fields.Char(string="Tipo de Documento de Transporte", help="Tipo de documento del transporte (ej: MATRICULA)")
    export_transport_document_number = fields.Char(string="Número de Documento de Transporte", help="Número del documento de transporte")
    export_transporter_processor = fields.Char(string="Transportadora", help="Nombre de la transportadora")
    export_merchandise_origin_country = fields.Char(string="País de Origen de la Mercancía", help="País de origen de la mercancía", default="COLOMBIA")
    export_destination = fields.Char(string="Destino", help="Ciudad o lugar de destino de la mercancía", compute="_compute_export_destination", store=True, readonly=False)
    export_payment_means = fields.Char(string="Forma de Pago", help="Forma de pago de la exportación", compute="_compute_export_payment_means", store=True, readonly=False)
    export_insurance_carrier = fields.Char(string="Aseguradora", help="Nombre de la aseguradora")
    export_observations = fields.Text(string="Observaciones", help="Observaciones adicionales para la exportación")

    # payroll
    ei_type_payroll_adjust_notes = fields.Selection([
        ('1', 'Reemplazar'),
        ('2', 'Eliminar'),
    ], string="Tipo de Nota de Ajuste de Nomina", default='2')

    # health / sector salud
    ei_is_invoice_health = fields.Boolean(string="¿Es factura de salud?", default=False)
    health_sector_user_ids = fields.One2many(
        'account.move.health.line', 'move_id', string=''
    )
    invoice_period_start_date = fields.Date(string="Fecha de inicio", help="Fecha de inicio del periodo relacionado con la factura")
    invoice_period_end_date = fields.Date(string="Fecha de fin", help="Fecha de fin del periodo relacionado con la factura")
    health_type_operation = fields.Selection([
        ('1', 'SS-CUFE'),
        ('2', 'SS-CUDE'),
        ('3', 'SS-POS'),
        ('4', 'SS-SNum'),
        ('5', 'SS-Recaudo'),
        ('6', 'SS-Reporte'),
        ('7', 'SS-SinAporte')
    ], string="Tipo de Operación", default='1', help="Tipo de operación del sector salud")

    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()

        for rec in self:
            amount_tax_withholding = 0
            amount_tax_withholding_company = 0
            amount_tax_no_withholding = 0
            amount_tax_no_withholding_company = 0
            amount_excluded = 0
            amount_excluded_company = 0
            amount_commercial_sample = 0
            amount_commercial_sample_company = 0

            rate = rec.currency_id.with_context(dict(rec._context or {}, date=rec.invoice_date)).rate
            inverse_rate = rec.currency_id.with_context(dict(rec._context or {}, date=rec.invoice_date)).inverse_rate
            for invoice_line_id in rec.invoice_line_ids:
                if invoice_line_id.account_id:
                    taxable_amount = invoice_line_id.price_subtotal
                    taxable_amount_company = abs(invoice_line_id.balance)
                    discount = bool(invoice_line_id.discount)

                    # If it is a commercial sample the taxable amount is zero and not discount but have lst_price
                    if not taxable_amount and not discount and invoice_line_id.product_id.lst_price:
                        # if rec.currency_id and rec.company_id and rec.currency_id != rec.company_id.currency_id:
                        #   raise UserError(
                        #       _("Commercial samples doesn't seem to be compatible with multi-currencies."))

                        lst_price_company = invoice_line_id.product_id.lst_price
                        lst_price_invoice = lst_price_company * rate

                        taxable_amount = lst_price_invoice * invoice_line_id.quantity
                        taxable_amount_company = lst_price_company * invoice_line_id.quantity

                        amount_commercial_sample = amount_commercial_sample + taxable_amount
                        amount_commercial_sample_company = amount_commercial_sample_company + taxable_amount_company

                    for invoice_line_tax_id in invoice_line_id.tax_ids:
                        tax_name = invoice_line_tax_id.description or ''
                        dian_report_tax_base = invoice_line_tax_id.dian_report_tax_base or 'auto'

                        if invoice_line_tax_id.amount_type == 'fixed':
                            # For fixed amount type
                            # The 'amount' field automatically uses the value defined in the tax configuration
                            # without currency conversion.
                            tax_amount = invoice_line_id.quantity * invoice_line_tax_id.amount
                            tax_amount_company = tax_amount * inverse_rate
                        else:
                            # For percent and code amount type
                            tax_amount = taxable_amount * invoice_line_tax_id.amount / 100.0
                            tax_amount_company = taxable_amount_company * invoice_line_tax_id.amount / 100.0

                        if invoice_line_tax_id.edi_tax_id.id:
                            edi_tax_name = invoice_line_tax_id.edi_tax_id.name
                            if tax_name.startswith(('IVA Excluido', 'IVA Compra Excluido')) or \
                                    (edi_tax_name == 'IVA' and dian_report_tax_base == 'no_report'):
                                amount_excluded = amount_excluded + taxable_amount
                                amount_excluded_company = amount_excluded_company + taxable_amount_company
                            elif edi_tax_name[:4] == 'Rete':
                                amount_tax_withholding = amount_tax_withholding + tax_amount
                                amount_tax_withholding_company = amount_tax_withholding_company + tax_amount_company
                            else:
                                amount_tax_no_withholding = amount_tax_no_withholding + tax_amount
                                amount_tax_no_withholding_company = (amount_tax_no_withholding_company +
                                                                     tax_amount_company)
                        else:
                            if tax_name.startswith(('IVA Excluido', 'IVA Compra Excluido')) or \
                                    (tax_name.startswith('IVA') and dian_report_tax_base == 'no_report'):
                                amount_excluded = amount_excluded + taxable_amount
                                amount_excluded_company = amount_excluded_company + taxable_amount_company
                            elif tax_name[:3] == 'Rte':
                                amount_tax_withholding = amount_tax_withholding + tax_amount
                                amount_tax_withholding_company = amount_tax_withholding_company + tax_amount_company
                            else:
                                amount_tax_no_withholding = amount_tax_no_withholding + tax_amount
                                amount_tax_no_withholding_company = (amount_tax_no_withholding_company +
                                                                     tax_amount_company)

            rec.ei_amount_tax_withholding = amount_tax_withholding
            rec.ei_amount_tax_withholding_company = amount_tax_withholding_company
            rec.ei_amount_tax_no_withholding = amount_tax_no_withholding
            rec.ei_amount_tax_no_withholding_company = amount_tax_no_withholding_company
            rec.ei_amount_total_no_withholding = rec.amount_untaxed + rec.ei_amount_tax_no_withholding
            rec.ei_amount_total_no_withholding_company = (abs(rec.amount_untaxed_signed) +
                                                          rec.ei_amount_tax_no_withholding_company)
            rec.ei_amount_excluded = amount_excluded
            rec.ei_amount_excluded_company = amount_excluded_company

            rec.ei_amount_commercial_sample = amount_commercial_sample
            rec.ei_amount_commercial_sample_company = amount_commercial_sample_company

            if self.is_universal_discount():
                # if rec.currency_id and rec.company_id and rec.currency_id != rec.company_id.currency_id:
                #     raise UserError(
                #         _("The universal discount module doesn't seem to be compatible with multi-currencies."))

                if not ('ks_global_tax_rate' in rec):
                    rec.ks_calculate_discount()
                sign = rec.move_type in ['in_refund', 'out_refund'] and -1 or 1
                rec.amount_residual_signed = rec.amount_total * sign
                rec.amount_total_signed = rec.amount_total * sign

                rec.ei_amount_total_no_withholding = (rec.amount_untaxed +
                                                      rec.ei_amount_tax_no_withholding -
                                                      rec.ks_amount_discount)
                rec.ei_amount_total_no_withholding_company = (abs(rec.amount_untaxed_signed) +
                                                              rec.ei_amount_tax_no_withholding_company -
                                                              rec.ks_amount_discount)

            # Value in letters
            decimal_part, integer_part = math.modf(abs(rec.ei_amount_total_no_withholding_company))
            if decimal_part:
                decimal_part = round(decimal_part * math.pow(10, rec.company_currency_id.decimal_places))
            if integer_part:
                if rec.company_id.electronic_invoicing_enabled :
                    lang = 'es_CO'
                else:
                    lang = rec.partner_id.lang if rec.partner_id.lang else 'en'

                rec.value_letters = (num2words(integer_part, lang=lang).upper() + ' ' +
                                     rec.company_currency_id.currency_unit_label.upper())
                if decimal_part:
                    rec.value_letters = (rec.value_letters + ', ' +
                                         num2words(decimal_part, lang=lang).upper() + ' ' +
                                         rec.company_currency_id.currency_subunit_label.upper() + '.')

    @api.depends('invoice_date', 'invoice_date_due')
    def _compute_payment_form_id(self):
        if not self.env['l10n_co_fl.payment.form'].search_count([]):
            self.env['res.company'].init_csv_data('l10n_co_catalog.l10n_co_fl.payment_form')

        for rec in self:
            if rec.invoice_date and rec.invoice_date_due:
                if rec.invoice_date >= rec.invoice_date_due:
                    # Cash
                    rec.payment_form_id = 1
                else:
                    # Credit
                    rec.payment_form_id = 2
            else:
                # Cash
                rec.payment_form_id = 1


    @api.depends('invoice_line_ids.price_unit', 'invoice_line_ids.is_global_discount')
    def get_discount_global(self):
        for rec in self:
            global_discount_lines = [line.price_unit for line in rec.invoice_line_ids if line.is_global_discount]
            rec.l10n_co_edi_discount_global = abs(sum(global_discount_lines) if global_discount_lines else 0.0)

    @api.depends('name', 'ref', 'journal_id')
    def compute_number_formatted(self):
        for rec in self:
            if rec.should_send_document_to_dian():
                prefix = rec.journal_id.prefix
                ei_number = ''
                number_formatted = ''

                if rec.name and prefix:
                    # Remove non-alphanumeric characters
                    name = re.sub(r'\W+', '', rec.name)
                    len_prefix = len(prefix)
                    len_name = len(name)

                    if 0 < len_prefix < len_name and name[0:len_prefix] == prefix:
                        number_unformatted = ''.join([i for i in name[len_prefix:] if i.isdigit()])
                        if number_unformatted:
                            ei_number = str(int(number_unformatted))
                            number_formatted = prefix + ei_number
                if ei_number and number_formatted:
                    rec.ei_number = ei_number
                    rec.number_formatted = number_formatted
                else:
                    rec.ei_number = ''
                    rec.number_formatted = ''
                    _logger.debug('Compute number format: Error.')
            elif rec.move_type in ('in_invoice', 'in_refund'):
                rec.ei_number = rec.ref
                rec.number_formatted = rec.ref
            else:
                rec.ei_number = ''
                rec.number_formatted = ''


    @api.depends('ei_is_correction_without_reference', 'debit_origin_id', 'journal_id','move_type','state')
    def _compute_ei_type_document(self):
        for rec in self:
            if rec.journal_id:
                print("######rec.journal_id######",rec.name)
                print("######rec.journal_id######",rec.journal_id.name)
                print("######rec.journal_id######",rec.ei_type_document_id.name)
                print("######rec.journal_id######",rec.ei_type_document_id.code)
                if rec.ei_type_document_id.code == '01':
                    rec.ei_type_document = 'invoice'
                elif rec.ei_type_document_id.code == '02':
                    rec.ei_type_document = 'export_invoice'
                elif rec.ei_type_document_id.code == '91':
                    rec.ei_type_document = 'credit_note'
                elif rec.ei_type_document_id.code == '92':
                    rec.ei_type_document = 'debit_note'
                elif rec.ei_type_document_id.code == '05':
                    rec.ei_type_document = 'doc_support'
                elif rec.ei_type_document_id.code == '95':
                    rec.ei_type_document = 'note_support'
                elif rec.ei_type_document_id.code == '1':
                    rec.ei_type_document = 'payroll'
                elif rec.ei_type_document_id.code == '2':
                    rec.ei_type_document = 'payroll_adjustment'
                else:
                    rec.ei_type_document = 'none'
            else:
                rec.ei_type_document = 'none'



    @api.model
    def is_universal_discount(self):
        try:
            if 'ks_amount_discount' in self:
                return bool(self.env['res.company'].search([('ks_enable_discount', '=', True)]))
            else:
                return False
        except KeyError:
            return False

    def action_view_edi_requests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Requests EDI',
            'view_mode': 'form',
            'res_model': 'co.request.edi',
            'res_id': self.request_edi.id,
            'context': {'default_invoice_id': self.id},
        }
    def should_send_document_to_dian(self):
        self.ensure_one()

        type_edi_document = self.ei_type_document
        print("######type_edi_document######", type_edi_document)
        if self.move_type in ('out_invoice', 'out_refund') and type_edi_document in (
                'invoice', 'credit_note', 'debit_note', 'note_support', 'export_invoice'):
            return True
        if self.move_type in ('in_invoice', 'in_refund') and type_edi_document in ('doc_support', 'note_support'):
            return True
        if self.move_type in ('entry') and type_edi_document in ('payroll', 'payroll_adjustment'):
            return True
        return False

    def validate_configuration(self):
        for record in self:
            company = self.get_parent_company()
            if record.state != 'posted':
                raise UserError("Solo se pueden enviar facturas Publicadas a la API, posiblemente esta en estado Borrador.")
            if not company.ip_domain:
                raise UserError("Dominio IP no disponible. Configure la empresa primero para obtener un dominio IP.")
            if not company.is_valid_company_config:
                raise UserError("Configuración de la empresa no válida. Por favor configure la empresa correctamente.")
            if not company.token:
                raise UserError("Token no disponible. Configure la empresa primero para obtener un token.")
            if not company.is_valid_certificate_config:
                raise UserError("Certificado no válido. Por favor configure un certificado válido.")
            if not company.is_valid_software_config:
                raise UserError("Software no válido. Por favor configure un software válido.")
            if not  record.journal_id.resolution_type_document_id:
                raise UserError("Por favor complete el tipo de documento antes de continuar.")
            if not record.journal_id.prefix:
                raise UserError("Por favor complete el prefijo antes de continuar.")
            if not self.ei_type_document in ('doc_support', 'credit_note', 'debit_note', 'payroll', 'note_support', 'payroll_adjustment'):
                if not record.journal_id.resolution:
                    raise UserError("Por favor complete la resolución antes de continuar.")
                if not record.journal_id.resolution_date:
                    raise UserError("Por favor complete la fecha de resolución antes de continuar.")
                if not record.journal_id.date_from:
                    raise UserError("Por favor complete la fecha desde antes de continuar.")
                if not record.journal_id.technical_key:
                    raise UserError("Por favor complete la clave técnica antes de continuar.")
                if not record.journal_id.date_to:
                    raise UserError("Por favor complete la fecha hasta antes de continuar.")
            if not record.journal_id.from_number:
                raise UserError("Por favor complete el número inicial antes de continuar.")
            if not record.journal_id.to_number:
                raise UserError("Por favor complete el número final antes de continuar.")
            if record.journal_id.from_number <= 0 or record.journal_id.to_number <= 0:
                raise UserError("Los números de resolución deben ser mayores que cero.")
            if record.journal_id.from_number >= record.journal_id.to_number:
                raise UserError("El número inicial debe ser menor que el número final.")
            if not record.journal_id.sequence_id:
                raise UserError("Por favor asigne una secuencia al diario antes de continuar.")
            if  record.journal_id.prefix not in record.journal_id.sequence_id.prefix:
                raise UserError("El prefijo de la secuencia no coincide con el prefijo de la resolución.")
            if record.journal_id.sequence_id.number_next_actual < record.journal_id.from_number:
                raise UserError("El número siguiente de la secuencia debe ser mayor o igual al número inicial de la resolución.")
            if not record.journal_id.is_valid_resolution_config:
                raise UserError("Configuración de resolución no válida. Por favor configure la resolución correctamente.")

    def current_date(self):
        tz = pytz.timezone('America/Bogota')
        if self.invoice_date:
            invoice_date = self.invoice_date
            current_time = datetime.now(tz).time()
            invoice_datetime = datetime.combine(invoice_date, current_time)
            invoice_datetime = tz.localize(invoice_datetime)
        else:
            invoice_datetime = datetime.now(tz)
        date_string = invoice_datetime.strftime('%Y-%m-%d')
        time_string = invoice_datetime.strftime('%H:%M:%S')
        return date_string, time_string

    def clean_nit(self,nit):
        return int(''.join(filter(str.isdigit, nit)))

    def calcular_dv(self,nit):
        nit = str(nit)
        factores = [3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71]
        nit_reversed = nit[::-1]
        suma = 0

        for i in range(len(nit_reversed)):
            suma += int(nit_reversed[i]) * factores[i]

        residuo = suma % 11
        if residuo == 0 or residuo == 1:
            dv = residuo
        else:
            dv = 11 - residuo

        return dv
    def validate_required_fields_customer(self,rec_partner):

        if not rec_partner.identification_co_number:
            raise UserError(_("El cliente debe disponer de un número de identificación."))
        if not rec_partner.l10n_co_edi_type_document_identification_id:
            raise UserError(_("El cliente debe disponer de un tipo de identificación DIAN."))

        # if not rec_partner.l10n_co_edi_type_organization_id:
        #     raise UserError(_("El cliente debe disponer de un tipo de organización."))
        # if not rec_partner.l10n_co_edi_type_liability_id:
        #     raise UserError(_("El cliente debe disponer de un tipo de responsabilidad."))
        # # For export invoices, municipality is not required
        # if not rec_partner.municipality_id and not self.is_out_country:
        #     raise UserError(_("El cliente debe disponer de un municipio."))
        # if not rec_partner.type_regime_id:
        #     raise UserError(_("El cliente debe disponer de un tipo de régimen."))
        # if not rec_partner.phone and not rec_partner.mobile:
        #     raise UserError(_("El cliente debe disponer de un teléfono."))
        if not rec_partner.email:
            raise UserError(_("El cliente debe disponer de un correo electrónico."))
        # if not rec_partner.street:
        #     raise UserError(_("El cliente debe disponer de una dirección."))

    def get_ei_customer(self):
        for record in self:
            customer = {}
            if record.partner_id.type == 'invoice' and record.partner_id.parent_id:
                rec_partner = record.partner_id.parent_id
            else:
                rec_partner = record.partner_id
            record.validate_required_fields_customer(rec_partner)
            l10n_co_edi_type_document_identification_id = rec_partner.l10n_co_edi_type_document_identification_id.id
            clean_identification_number = record.clean_nit(rec_partner.identification_co_number)
            if clean_identification_number:
                customer['identification_number'] = clean_identification_number
            if l10n_co_edi_type_document_identification_id == 6:
                customer['dv'] = record.calcular_dv(clean_identification_number)
            if rec_partner.name:
                customer['name'] = rec_partner.name

            # Use phone if available, otherwise use mobile
            phone = False
            if record.partner_id.phone:
                phone = record.partner_id.phone
            elif record.partner_id.mobile:
                phone = record.partner_id.mobile

            # Format and add phone to customer data if available
            if phone:
                if phone[:3] == '+57':
                    temp_phone = ''.join([i for i in phone[3:] if i.isdigit()])
                    phone = temp_phone
                customer['phone'] = phone

            if record.partner_id.street:
                address = record.partner_id.street.split(',')[0]
                if address:
                    customer['address'] = address
            if record.partner_id.email:
                customer['email'] = record.partner_id.email
            if rec_partner.l10n_co_edi_merchant_registration:
                merchant_registration = rec_partner.l10n_co_edi_merchant_registration
            else:
                merchant_registration = 'No tiene'
            customer['merchant_registration'] = merchant_registration

            if l10n_co_edi_type_document_identification_id:
                customer['type_document_identification_id'] = l10n_co_edi_type_document_identification_id
            type_organization_id = 1 if rec_partner.is_company else 2
            if type_organization_id:
                customer['type_organization_id'] = type_organization_id
            if rec_partner.l10n_co_edi_type_liability_id:
                customer['type_liability_id'] = rec_partner.l10n_co_edi_type_liability_id.id
            if rec_partner.municipality_id and not record.is_out_country:
                customer['municipality_id'] = rec_partner.municipality_id.id
                if record.ei_type_document in ('doc_support', 'note_support'):
                    customer['postal_zone_code'] = rec_partner.municipality_id.code
                    customer['dv'] = record.calcular_dv(clean_identification_number)
            if rec_partner.type_regime_id:
                customer['type_regime_id'] = rec_partner.type_regime_id.id

            if self.ei_type_document == 'export_invoice':
                dian_country = self.env['l10n_co_fl.country'].search([('code', '=', rec_partner.country_id.code)], limit=1)
                if dian_country:
                    customer['country_id'] = dian_country.id
                else:
                    raise UserError(_("El país del cliente (%s) no tiene una correspondencia en el catálogo DIAN de países.") % rec_partner.country_id.name)
                customer['state_name'] = rec_partner.state_id.name
                customer['municipality_name'] = rec_partner.city

            return customer
    def get_ei_payment_form(self):
        for rec in self:
            if rec.invoice_date and rec.invoice_date_due:
                if rec.invoice_date >= rec.invoice_date_due:
                    # Cash
                    duration_measure = 0
                else:
                    # Credit
                    duration_measure = (rec.invoice_date_due - rec.invoice_date).days
                payment_due_date = fields.Date.to_string(rec.invoice_date_due)
            else:
                _logger.debug("La factura o fecha de pago no es válida")
                # Cash
                duration_measure = 0
                payment_due_date = fields.Date.to_string(rec.invoice_date)

            return {
                'payment_form_id': rec.payment_form_id.id,
                'payment_method_id': rec.payment_method_id.id,
                'payment_due_date': payment_due_date,
                'duration_measure': duration_measure
            }


    def get_ei_legal_monetary_totals(self):
        self.ensure_one()
        line_extension_amount = abs(self.amount_untaxed_signed)
        tax_exclusive_amount = abs(
            self.amount_untaxed_signed) - self.ei_amount_excluded_company + self.ei_amount_commercial_sample_company

        allowance_total_amount = 0.0
        if self.l10n_co_edi_discount_global:
            if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
                raise UserError(
                    _("El módulo de descuento universal no parece ser compatible con múltiples monedas."))

            allowance_total_amount = self.l10n_co_edi_discount_global

        charge_total_amount = 0.0
        payable_amount = self.ei_amount_total_no_withholding_company
        tax_inclusive_amount = payable_amount - charge_total_amount + allowance_total_amount
        data = {"line_extension_amount": line_extension_amount + allowance_total_amount if allowance_total_amount else line_extension_amount,
                "tax_exclusive_amount": tax_exclusive_amount + allowance_total_amount if allowance_total_amount else tax_exclusive_amount,
                "tax_inclusive_amount": tax_inclusive_amount,
                "payable_amount": payable_amount
                }
        if self.l10n_co_edi_discount_global:
            data.update({"allowance_total_amount": allowance_total_amount})
        return data

    def get_ei_payroll_payload(self):
        payload = {}

        for record in self:
            move = record
            payslip = self.env['hr.payslip'].search([('number', '=', move.ref)], limit=1)

            # Depuración: Ver si se encontró el payslip
            if not payslip:
                raise UserError(f"No se encontró un payslip con número: {move.ref}")

            payload.update({
                'prefix': payslip.journal_id.prefix,
                'consecutive': move.sequence_number,
                'type_document_id': move.ei_type_document_id.id,
                'establishment_name': move.journal_id.edi_establishment_id.name,
                'establishment_address': move.journal_id.edi_establishment_id.address,
                'establishment_phone': move.journal_id.edi_establishment_id.phone,
                'establishment_municipality': move.journal_id.edi_establishment_id.municipality_id.id,
                'establishment_email': move.journal_id.edi_establishment_id.email,
                'novelty': {
                    'novelty': False,
                    'uuidnov': ''
                },
                'sendmail': False,
                'sendmailtome': False,
                'notes': '',
            })

            employee = payslip.employee_id
            contract = payslip.contract_id

            # Período de liquidación
            payload.update({
                'period': {
                    'admision_date': contract.date_start.strftime('%Y-%m-%d'),
                    'settlement_start_date': payslip.date_from.strftime('%Y-%m-%d'),
                    'settlement_end_date': payslip.date_to.strftime('%Y-%m-%d'),
                    'worked_time': str(sum(payslip.worked_days_line_ids.mapped('number_of_hours'))),
                    'issue_date': move.date.strftime('%Y-%m-%d'),
                }
            })

            payload.update({
                'worker_code': contract.name,
                'payroll_period_id': contract.ei_schedule_pay,
                'worker': {
                    'type_worker_id': contract.ei_type_worker_id,
                    'sub_type_worker_id': contract.ei_sub_type_worker_id,
                    'payroll_type_document_identification_id': employee.ei_type_document_identification_id.id,
                    'municipality_id': employee.private_state_id.id,
                    'type_contract_id': contract.ei_contract_type_id,
                    'high_risk_pension': False,
                    'identification_number': employee.identification_id,
                    'surname': employee.ei_surname,
                    'second_surname': employee.ei_second_surname,
                    'first_name': employee.ei_first_name,
                    'middle_name': employee.ei_middle_name,
                    'address': employee.private_street,
                    'integral_salarary': False,
                    'salary': str(contract.wage),
                    'email': employee.work_email,
                }
            })

            # Método de pago
            payload.update({
                'payment': {
                    'payment_method_id': move.payment_method_id.id,
                    # 'bank_name': move.bank_account_id.bank_id.name,
                    # 'account_type': move.bank_account_id.acc_type,
                    # 'account_number': move.bank_account_id.acc_number,
                }
            })

            # Fechas de pago
            payload.update({
                'payment_dates': [{'payment_date': move.date.strftime('%Y-%m-%d')}]
            })

            # Ingresos (accrued)
            total_salary = sum(payslip.line_ids.filtered(lambda l: l.category_id.code == 'BASIC').mapped('total'))
            # transport_allowance = sum(payslip.line_ids.filtered(lambda l: l.category_id.code == 'TRANSP').mapped('total'))
            transport_allowance = sum(payslip.line_ids.filtered(lambda l: l.code == 'TRANSP').mapped('total'))
            total_accrued = total_salary + transport_allowance

            payload.update({
                'accrued': {
                    'worked_days': sum(payslip.worked_days_line_ids.mapped('number_of_days')),
                    'salary': str(total_salary),
                    'transportation_allowance': str(transport_allowance),
                    'accrued_total': str(total_accrued),
                }
            })

            # Cesantias
            severance_lines = payslip.line_ids.filtered(lambda l: l.code == 'SEVERANCE')
            severance_data = []

            for line in severance_lines:
                severance_data.append({
                    "payment": str(line.total),
                    "percentage": str(line.rate),
                    "interest_payment": str(line.total * (line.rate / 100))
                })
            if severance_data:
                payload['accrued']['severance'] = severance_data

            # Obtener valores de Other Inputs
            withdrawal_bonus = sum(payslip.input_line_ids.filtered(lambda i: i.code == 'WITHDRAWAL_BONUS').mapped('amount'))
            service_bonus = sum(payslip.input_line_ids.filtered(lambda i: i.code == 'SERVICE_BONUS').mapped('amount'))

            service_bonus_data = [{
                "quantity": 365,
                "payment": str(service_bonus),
                "paymentNS": str(withdrawal_bonus)  # Prima No Salarial
            }]

            if service_bonus > 0:
                payload['accrued']['service_bonus'] = service_bonus_data

            if withdrawal_bonus > 0:
                payload['accrued']['withdrawal_bonus'] = str(withdrawal_bonus)

            # Deducciones
            eps_deduction = sum(payslip.line_ids.filtered(lambda l: l.code == 'EPS').mapped('total'))
            pension_deduction = sum(payslip.line_ids.filtered(lambda l: l.code == 'AFP').mapped('total'))
            total_deductions = eps_deduction + pension_deduction

            payload.update({
                'deductions': {
                    'eps_type_law_deductions_id': 1,
                    'eps_deduction': str(eps_deduction),
                    'pension_type_law_deductions_id': 5,
                    'pension_deduction': str(pension_deduction),
                    'deductions_total': str(total_deductions),
                }
            })
        return payload

    def get_ei_payroll_payload_adjustment(self):
        payload = {}

        for record in self:
            move = record
            payslip = self.env['hr.payslip'].search([('number', '=', move.reversed_entry_id.ref)], limit=1)
            contract = payslip.contract_id
            origin_payroll = move.reversed_entry_id

            # Depuración: Ver si se encontró el payslip
            if not payslip:
                raise UserError(f"No se encontró un payslip con número: {move.reversed_entry_id.ref}")

            payload.update({
                'prefix': move.journal_id.prefix,
                'consecutive': move.sequence_number,
                'type_document_id': move.ei_type_document_id.id,
                'establishment_name': move.journal_id.edi_establishment_id.name,
                'establishment_address': move.journal_id.edi_establishment_id.address,
                'establishment_phone': move.journal_id.edi_establishment_id.phone,
                'establishment_municipality': move.journal_id.edi_establishment_id.municipality_id.id,
                'establishment_email': move.journal_id.edi_establishment_id.email,
                'notes': '',
                'predecessor' : {
                    'predecessor_number': origin_payroll.sequence_number,
                    'predecessor_cune': origin_payroll.ei_uuid,
                    'predecessor_issue_date': origin_payroll.date.strftime('%Y-%m-%d')
                },
                'period': {
                    'admision_date': contract.date_start.strftime('%Y-%m-%d'),
                    'settlement_start_date': payslip.date_from.strftime('%Y-%m-%d'),
                    'settlement_end_date': payslip.date_to.strftime('%Y-%m-%d'),
                    'worked_time': str(sum(payslip.worked_days_line_ids.mapped('number_of_hours'))),
                    'issue_date': move.date.strftime('%Y-%m-%d'),
                },
                'payroll_period_id': contract.ei_schedule_pay,
                'type_note': 2,
            })
            # move.ei_type_payroll_adjust_notes no se guarda debido al reaonly de la variable en la vista de formulario
        return payload

    def calculate_supplement_values(self):
        """
        Calculate values for k_supplement dictionary based on invoice data,
        using the appropriate currency and formatting.
        """
        self.ensure_one()

        # Format a number to two decimal places as string
        def format_amount(amount):
            return "{:.2f}".format(amount)

        # Calculate base values
        subtotal = abs(self.amount_untaxed)
        discount = self.l10n_co_edi_discount_global if self.l10n_co_edi_discount_global else 0.0
        surcharge = 0.0  # No surcharge in standard implementation

        # Tax calculations - initialize values
        vat_taxes = 0.0
        consumption_taxes = 0.0  # Impuesto al consumo
        bag_taxes = 0.0  # Impuesto de bolsas
        other_taxes = 0.0

        # Calculate different types of taxes using the invoice lines directly
        for invoice_line in self.invoice_line_ids.filtered(lambda l: l.account_id and not l.is_global_discount):
            taxable_amount = invoice_line.price_subtotal

            for tax in invoice_line.tax_ids:
                tax_amount = taxable_amount * tax.amount / 100.0 if tax.amount_type == 'percent' else invoice_line.quantity * tax.amount

                # Check if tax has EDI tax ID
                if tax.edi_tax_id:
                    edi_tax_name = tax.edi_tax_id.name.lower()
                    tax_description = (tax.description or '').lower()

                    # Classify taxes based on name/description
                    if 'iva' in edi_tax_name and 'rete' not in edi_tax_name and 'exclu' not in tax_description:
                        vat_taxes += tax_amount
                    elif 'consumo' in edi_tax_name:
                        consumption_taxes += tax_amount
                    elif 'bolsa' in edi_tax_name:
                        bag_taxes += tax_amount
                    elif 'rete' not in edi_tax_name:
                        other_taxes += tax_amount

        # Get withholding values directly from computed fields
        withholding_taxes = abs(self.ei_amount_tax_withholding)
        withholding_vat = 0.0  # ReteIVA - would need specific calculation
        withholding_municipal = 0.0  # ReteICA - would need specific calculation

        # Total taxes
        total_taxes = vat_taxes + consumption_taxes + bag_taxes + other_taxes

        # Gross total (before taxes)
        total_gross = subtotal

        # Net total (including taxes)
        total_net = subtotal + total_taxes

        # Total payable (net minus withholdings and discounts)
        total_payable = total_net - discount

        # Advances - not part of standard implementation
        advances = 0.0

        return {
            "SubTotalCop": format_amount(subtotal),
            "DescuentoDetalleCop": format_amount(discount),
            "RecargoDetalleCop": format_amount(surcharge),
            "TotalBrutoFacturaCop": format_amount(total_gross),
            "TotIvaCop": format_amount(vat_taxes),
            "TotIncCop": format_amount(consumption_taxes),
            "TotBolCop": format_amount(bag_taxes),
            "ImpOtroCop": format_amount(other_taxes),
            "MntImpCop": format_amount(total_taxes),
            "TotalNetoFacturaCop": format_amount(total_net),
            "MntDctoCop": format_amount(discount),
            "MntRcgoCop": format_amount(surcharge),
            "VlrPagarCop": format_amount(total_payable),
            "ReteFueCop": format_amount(withholding_taxes),
            "ReteIvaCop": format_amount(withholding_vat),
            "ReteIcaCop": format_amount(withholding_municipal),
            "TotAnticiposCop": format_amount(advances)
        }

    def prepare_invoice_payload(self):
        for record in self:

            if record.should_send_document_to_dian():
                if not record.ei_number or not record.number_formatted:
                    record.compute_number_formatted()
                date_string, time_string  = record.current_date()
                payload = {}

                # TO DO : separar a otro metodo la generacion del json
                if record.ei_type_document == 'export_invoice':
                    # Validate that incoterm is set for export invoices
                    if not hasattr(record, 'invoice_incoterm_id') or not record.invoice_incoterm_id:
                        raise UserError(_("Para facturas de exportación, el campo Incoterm es obligatorio."))

                    # Add incoterm information
                    incoterm_code = record.invoice_incoterm_id.code or ''
                    incoterm_name = record.invoice_incoterm_id.name or ''
                    special_terms = f"{incoterm_name} ({incoterm_code})" if incoterm_code else incoterm_name

                    payload.update({
                        'deliveryterms': {
                            "special_terms": special_terms,
                            "loss_risk_responsibility_code": incoterm_code,
                            "loss_risk": incoterm_name
                        }
                    })

                    # Calculate supplement values using the function
                    supplement_values = record.calculate_supplement_values()

                    # Get values from the model fields or use defaults
                    responsible_incharge = record.export_responsible_incharge or 'Ninguno'
                    departure_place = record.export_departure_place or 'Ninguno'
                    conveyance = record.export_conveyance or 'Ninguno'
                    transport_document_type = record.export_transport_document_type or 'Ninguno'
                    transport_document_number = record.export_transport_document_number or 'Ninguno'
                    transporter_processor = record.export_transporter_processor or 'Ninguno'
                    merchandise_origin_country = record.export_merchandise_origin_country or 'Ninguno'
                    destination = record.export_destination or 'Ninguno'
                    payment_means = record.export_payment_means or 'Ninguno'
                    insurance_carrier = record.export_insurance_carrier or 'Ninguno'
                    observations = record.export_observations or 'Ninguna'

                    payload.update({
                        'k_supplement': {
                            "MonedaCop": record.currency_id.name,
                            "FctConvCop": str(record.currency_id.inverse_rate),
                            "responsible_incharge": responsible_incharge,
                            "departure_place": departure_place,
                            "conveyance": conveyance,
                            "transport_document_type": transport_document_type,
                            "transport_document_number": transport_document_number,
                            "transporter_processor": transporter_processor,
                            "merchandise_origin_country": merchandise_origin_country,
                            "destination": destination,
                            "payment_means": payment_means,
                            "insurance_carrier": insurance_carrier,
                            "observations": observations,
                            **supplement_values
                        }
                    })

                if record.ei_type_document == 'payroll':
                    payload = record.get_ei_payroll_payload()
                    return payload

                if record.ei_type_document == 'payroll_adjustment':
                    payload = record.get_ei_payroll_payload_adjustment()
                    return payload

                payload.update({
                    'number': record.ei_number,
                    'type_document_id': record.ei_type_document_id.id,
                    'date': date_string,
                    'time': time_string,
                    'resolution_number': record.journal_id.resolution,
                    'prefix': record.journal_id.prefix,
                })
                # if record.ei_type_document=='debit_note':
                #     payload.pop('prefix')
                # Asegurarse de que record.narration sea una cadena
                narration = record.narration if isinstance(record.narration, str) else ''
                # Eliminar etiquetas HTML de la narración
                clean_narration = re.sub(r'<.*?>', '', narration)
                if clean_narration:
                    payload.update({'notes': clean_narration})

                if record.journal_id.edi_establishment_id:
                    payload.update({
                        'establishment_id': record.journal_id.edi_establishment_id.name,
                        'establishment_address': record.journal_id.edi_establishment_id.address,
                        'establishment_phone': record.journal_id.edi_establishment_id.phone,
                        'establishment_municipality_id': record.journal_id.edi_establishment_id.municipality_id.id,
                        'establishment_email': record.journal_id.edi_establishment_id.email,
                    })
                company = record.get_parent_company()
                if company.use_api_mail_server:
                # Build email list including main partner and child contacts
                    email_list = []

                    # Add main partner email
#                    if record.partner_id.email:
#                        email_list.append({'email': record.partner_id.email})

                    # Add child contacts emails
                    if record.partner_id.child_ids:
                        for child in record.partner_id.child_ids:
                            if child.email and child.email not in [email['email'] for email in email_list]:
                                email_list.append({'email': child.email})

                    payload.update({
                        'sendmail': True,
                        'sendmailtome': True,
                        'send_customer_credentials': True,
                        'email_cc_list': email_list,
                    })
                else:
                    payload.update({
                        'sendmail': False,
                        'sendmailtome': False,
                        'send_customer_credentials':False
                    })
                if not record.ei_type_document in ('doc_support', 'note_support'):
                    payload.update({'customer': record.get_ei_customer()})
                else:
                    payload.update({'seller': record.get_ei_customer()})
                if record.ei_type_document == 'invoice':
                    payload['payment_form'] = record.get_ei_payment_form()

                if not  record.ei_type_document == 'debit_note':
                    payload.update({'legal_monetary_totals': record.get_ei_legal_monetary_totals()})
                else:
                   payload.update({'requested_monetary_totals': record.get_ei_legal_monetary_totals()})
                billing_reference = False
                type_edi_document = record.ei_type_document
                invoice_rec = None
                get_ei_lines = record.get_ei_lines()

                # TO DO : separar a otro metodo la generacion del json
                # Si es una factura del sector salud
                if record.ei_is_invoice_health:
                    health_fields = {
                        "invoice_period_start_date": record.invoice_period_start_date.strftime('%Y-%m-%d') if record.invoice_period_start_date else "",
                        "invoice_period_end_date": record.invoice_period_end_date.strftime('%Y-%m-%d') if record.invoice_period_end_date else "",
                        "health_type_operation_id": record.health_type_operation,
                        "print_users_info_to_pdf": True,
                        "users_info": []
                    }

                    # Construir la lista de usuarios del sector salud
                    for user in record.health_sector_user_ids:
                        user_info = {
                            "provider_code": user.provider_code,
                            "health_type_document_identification_id": int(user.health_type_document_identification_id),
                            "identification_number": user.identification_number,
                            "surname": user.surname,
                            "second_surname": user.second_surname,
                            "first_name": user.first_name,
                            "middle_name": user.middle_name,
                            "health_type_user_id": int(user.health_type_user_id),
                            "health_contracting_payment_method_id": int(user.health_contracting_payment_method_id),
                            "health_coverage_id": int(user.health_coverage_id),
                            "autorization_numbers": user.autorization_numbers,
                            "mipres": user.mipres,
                            "mipres_delivery": user.mipres_delivery,
                            "contract_number": user.contract_number,
                            "policy_number": user.policy_number,
                            "co_payment": user.co_payment,
                            "moderating_fee": user.moderating_fee,
                            "recovery_fee": user.recovery_fee,
                            "shared_payment": user.shared_payment
                        }
                        health_fields["users_info"].append(user_info)

                    # Agregar los campos de salud al payload
                    payload["health_fields"] = health_fields

                print("######get_ei_lines######", get_ei_lines)
                payload['tax_totals'] = get_ei_lines['tax_totals_info']
                payload['with_holding_tax_total'] = get_ei_lines['with_holding_tax_total']
                if record.ei_type_document in ('invoice', 'doc_support', 'export_invoice'):
                    payload['invoice_lines'] = get_ei_lines['lines']
                elif record.ei_type_document in ('credit_note', 'note_support'):
                    payload['credit_note_lines'] = get_ei_lines['lines']
                elif record.ei_type_document == 'debit_note':
                    payload['debit_note_lines'] = get_ei_lines['lines']
                if not company.currency_id or company.currency_id.name != 'COP':
                    raise UserError(_('La moneda de la empresa debe ser COP para reportar facturas a la DIAN.'
                                      'Configúrelo en la vista de configuración de Empresas en Odoo.'))


                if type_edi_document in ('invoice', 'doc_support', 'export_invoice'):
                    # Sales invoice
                    billing_reference = False
                elif type_edi_document == 'note_support':
                    # Credit note
                    invoice_env = self.env['account.move']
                    invoice_rec = invoice_env.search([('id', '=', record.reversed_entry_id.id)])
                    billing_reference = True
                elif type_edi_document == 'credit_note':
                    # si hay relacion con una factura
                    if not record.ei_is_correction_without_reference:
                        invoice_env = self.env['account.move']
                        invoice_rec = invoice_env.search([('id', '=', record.reversed_entry_id.id)])
                        billing_reference = True
                    else:
                        if not record.ei_period_start_date or not record.ei_period_end_date:
                            raise UserError("Debe seleccionar el periodo de fechas (Inicio y Fin) para la Nota de Credito.")
                        start_date = record.ei_period_start_date.strftime('%Y-%m-%d')
                        end_date = record.ei_period_end_date.strftime('%Y-%m-%d')
                        invoice_period = {
                            "start_date": start_date,
                            "end_date": end_date
                        }
                        payload['invoice_period'] = invoice_period
                        payload['type_operation_id'] = "8"
                        payload.pop('resolution_number', None)
                        billing_reference = False
                elif type_edi_document == 'debit_note':
                    # Las notas débito siempre requieren una referencia a un documento
                    invoice_env = self.env['account.move']
                    invoice_rec = invoice_env.search([('id', '=', record.debit_origin_id.id)])
                    billing_reference = True

                if billing_reference:


                    if record.ei_correction_concept_credit_id:
                        payload['discrepancyresponsecode']= record.ei_correction_concept_credit_id.id
                        payload['discrepancyresponsedescription']=record.ei_correction_concept_credit_id.name
                    elif record.ei_correction_concept_debit_id:
                        payload['discrepancyresponsecode']= record.ei_correction_concept_debit_id.id
                        payload['discrepancyresponsedescription']=record.ei_correction_concept_debit_id.name
                    else:
                        raise UserError(_("You need to select a correction code first"))

                    # Para notas débito, siempre usamos referencias, independientemente del valor de ei_is_correction_without_reference
                    if type_edi_document == 'debit_note' or not record.ei_is_correction_without_reference:
                        if invoice_rec and invoice_rec.ei_uuid:

                            billing_reference_dic={
                                "number": invoice_rec.name,
                                "uuid": invoice_rec.ei_uuid,
                                "issue_date": fields.Date.to_string(invoice_rec.invoice_date)
                            }
                            payload['billing_reference'] = billing_reference_dic

                        else:
                            raise UserError(_("La factura de referencia aún no ha sido validada ante la DIAN"))
                    elif type_edi_document == 'note_support':
                        raise UserError(
                            _("La nota de crédito por soporte documental no puede ser una corrección sin referencia"))

                if record.l10n_co_edi_discount_global:
                    if record.currency_id and company and record.currency_id != company.currency_id:
                        raise UserError(
                            _("El módulo de descuento universal no parece ser compatible con múltiples monedas."))


                    allowance_charges = []
                    allowance_charge = {
                        'discount_id': 1,
                        'charge_indicator': False,
                        'allowance_charge_reason': 'Descuento general',
                        'amount': str(self.l10n_co_edi_discount_global),
                        'base_amount': str(abs(record.amount_total)+ self.l10n_co_edi_discount_global),


                    }
                    allowance_charges.append(allowance_charge)
                    payload['allowance_charges'] = allowance_charges
            else:
                raise UserError(_("Este tipo de documento no necesita ser enviado a la DIAN"))
            return payload

    def get_ei_lines(self):
        self.ensure_one()

        lines = []
        round_curr = self.company_currency_id.round
        tax_totals_info = []
        with_holding_tax_total = []  # Lista para almacenar retenciones
        for invoice_line_id in self.invoice_line_ids.filtered(lambda x: not x.is_global_discount):
            if invoice_line_id.account_id:
                if not (0 <= invoice_line_id.discount < 100):
                    raise UserError(_("El descuento siempre debe ser mayor o igual a 0 y menor a 100."))

                price_unit = 100.0 * abs(invoice_line_id.balance) / (invoice_line_id.quantity * (
                        100.0 - invoice_line_id.discount))
                invoice_temps = {}
                products = {}
                products.update({'free_of_charge_indicator':False})
                allowance_charges = {}
                tax_totals = {'tax_totals': []}
                products.update({'price_amount': str(price_unit)})
                # products.update({'price_amount': invoice_line_id.price_total})
                products.update({'base_quantity': str(abs(invoice_line_id.quantity))})

                if invoice_line_id.product_id.code:
                    products.update({'code': invoice_line_id.product_id.code})
                else:
                    raise UserError(_("Todos los productos deben tener una referencia interna asignada"))



                products.update({'description': invoice_line_id.name})

                # Check if this is an export invoice and validate brand/model
                if self.is_out_country:
                    if not invoice_line_id.product_id.brandname:
                        raise UserError(_("Para facturas de exportación, el campo 'Marca' es obligatorio en todos los productos."))
                    if not invoice_line_id.product_id.modelname:
                        raise UserError(_("Para facturas de exportación, el campo 'Modelo' es obligatorio en todos los productos."))

                # Add brand and model information
                if invoice_line_id.product_id.brandname:
                    products.update({'brandname': invoice_line_id.product_id.brandname})
                if invoice_line_id.product_id.modelname:
                    products.update({'modelname': invoice_line_id.product_id.modelname})

                if invoice_line_id.ei_notes:
                    products.update({'notes':invoice_line_id.ei_notes})
                    # products.update({'notes': [{'text': invoice_line_id.ei_notes if invoice_line_id.ei_notes else invoice_line_id.name}]})

                if invoice_line_id.product_uom_id.edi_unit_measure_id.id:
                    products.update({'unit_measure_id': invoice_line_id.product_uom_id.edi_unit_measure_id.id})
                else:
                    raise UserError(_("A todos los productos se les debe asignar una unidad de medida (DIAN)"))

                products.update({'invoiced_quantity': str(abs(invoice_line_id.quantity))})
                products.update({'line_extension_amount': str(abs(invoice_line_id.balance))})
                # TODO: Standard product codes compatibility
                # [4]: Taxpayer adoption standard ('999')
                if invoice_line_id.product_id.type_item_identification_id:
                    products.update({'type_item_identification_id': invoice_line_id.product_id.type_item_identification_id.id})

                else:
                    products.update({'type_item_identification_id': 4})

                # Discounts
                if invoice_line_id.discount:
                    discount = True
                    allowance_charges.update({'charge_indicator': False})
                    amount = abs(invoice_line_id.balance) * invoice_line_id.discount / (
                            100.0 - invoice_line_id.discount)
                    base_amount = abs(invoice_line_id.balance) + amount
                    allowance_charge_reason = "Descuento"
                else:
                    discount = False
                    allowance_charges.update({'charge_indicator': False})
                    amount = 0
                    base_amount = 0
                    allowance_charge_reason = ""

                taxable_amount_company = abs(invoice_line_id.balance)

                # If it is a commercial sample the taxable amount is zero and not discount but have lst_price
                commercial_sample = False
                if not taxable_amount_company and not discount and invoice_line_id.product_id.lst_price:
                    if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
                        raise UserError(
                            _("Commercial samples doesn't seem to be compatible with multi-currencies."))

                    # Use the following code, as an example, to configure the tax for a commercial sample.
                    # For this you must install the account_tax_python module and
                    # select the "Tax computation" field as "Python code" in the tax form.
                    #
                    # In the "Python code" field, in the tax form; for 19% tax:
                    #
                    # if price_unit:
                    #     result = price_unit * quantity * 0.19
                    # else:
                    #     result = product.lst_price * quantity * 0.19
                    #
                    commercial_sample = True
                    products.update({'price_code': 1})  # Commercial value ('01')
                    taxable_amount_company = invoice_line_id.product_id.lst_price * invoice_line_id.quantity
                    products.update({'price_amount': invoice_line_id.product_id.lst_price})

                allowance_charges.update({'base_amount': base_amount})
                allowance_charges.update({'amount': amount})
                allowance_charges.update({'allowance_charge_reason': allowance_charge_reason})

                # Calculate tax totals for invoice line
                for invoice_line_tax_id in invoice_line_id.tax_ids:
                    tax_total = {}

                    if invoice_line_tax_id.edi_tax_id.id:
                        edi_tax_name = invoice_line_tax_id.edi_tax_id.name
                        tax_name = invoice_line_tax_id.description or ''
                        dian_report_tax_base = invoice_line_tax_id.dian_report_tax_base or 'auto'
                        # The information sent to DIAN should not include the withholdings
                        if edi_tax_name[:4] != 'Rete' \
                                and not tax_name.startswith(('IVA Excluido', 'IVA Compra Excluido')) \
                                and not (edi_tax_name == 'IVA' and dian_report_tax_base == 'no_report'):
                            if invoice_line_tax_id.amount_type == 'percent':
                                tax_total.update({'tax_id': invoice_line_tax_id.edi_tax_id.id})
                                tax_total.update({'tax_amount': round_curr(
                                    taxable_amount_company * invoice_line_tax_id.amount / 100.0)})
                                tax_total.update({'taxable_amount': round_curr(taxable_amount_company)})
                                tax_total.update({'percent': invoice_line_tax_id.amount})
                                tax_totals['tax_totals'].append(tax_total)
                                tax_totals_info.append(tax_total)
                            elif invoice_line_tax_id.amount_type == 'fixed':
                                tax_total.update({'tax_id': invoice_line_tax_id.edi_tax_id.id})
                                tax_total.update({'tax_amount': round_curr(
                                    invoice_line_id.quantity * invoice_line_tax_id.amount)})
                                tax_total.update({'taxable_amount': invoice_line_id.quantity})
                                # "886","number of international units","NIU"
                                tax_total.update({'uom_code': 886})
                                tax_total.update({'unit_value': round_curr(invoice_line_tax_id.amount)})
                                tax_total.update({'base_uom': "1.000000"})
                                tax_totals['tax_totals'].append(tax_total)
                                tax_totals_info.append(tax_total)
                            elif invoice_line_tax_id.amount_type == 'tax_id':
                                # For now, only compatible with percentage taxes
                                if commercial_sample:
                                    tax_total.update({'tax_id': invoice_line_tax_id.edi_tax_id.id})
                                    tax_total.update({'tax_amount': round_curr(invoice_line_id.price_total)})
                                    tax_total.update({'taxable_amount': round_curr(taxable_amount_company)})
                                    # The tax is rounded to 0 decimal places, integers. In case of rounding issues,
                                    # it is expected that this will be sufficient to correct the problem and at the
                                    # same time cover all possible percentage tax values for Colombia.
                                    tax_total.update({'percent': round(
                                        invoice_line_id.price_total / taxable_amount_company * 100)})
                                    tax_totals['tax_totals'].append(tax_total)
                                    tax_totals_info.append(tax_total)
                                else:
                                    tax_total.update({'tax_id': invoice_line_tax_id.edi_tax_id.id})
                                    tax_total.update({'tax_amount': round_curr(
                                        taxable_amount_company * invoice_line_tax_id.amount / 100.0)})
                                    tax_total.update({'taxable_amount': round_curr(taxable_amount_company)})
                                    tax_total.update({'percent': invoice_line_tax_id.amount})
                                    tax_totals['tax_totals'].append(tax_total)
                                    tax_totals_info.append(tax_total)
                            else:
                                raise UserError(_("Electronic invoicing is not yet compatible with this tax type."))
                        if edi_tax_name[:4] == 'Rete':
                            tax_total.update({'tax_id': invoice_line_tax_id.edi_tax_id.id})
                            tax_total.update({'tax_amount': str(round_curr(abs(taxable_amount_company * invoice_line_tax_id.amount / 100.0)))})
                            tax_total.update({'taxable_amount': str(round_curr(abs(taxable_amount_company)))})
                            tax_total.update({'percent': str(abs(invoice_line_tax_id.amount))})
                            with_holding_tax_total.append(tax_total)

                    else:
                        raise UserError(_("A todos los impuestos se les debe asignar un tipo de impuesto (DIAN)."))

                # UPDATE ALL THE ELEMENTS OF THE PRODUCT
                invoice_temps.update(products)

                # UPDATE ALL PRODUCT DISCOUNTS (* ONLY ONE IS SUPPOSED *)
                if discount:
                    invoice_temps.update({'allowance_charges': [allowance_charges]})

                # Taxes are attached inside this json
                if tax_totals['tax_totals']:
                    invoice_temps.update({'tax_totals': tax_totals['tax_totals']})

                if self.ei_type_document_id.id == 11:
                    invoice_temps.update(
                        {'type_generation_transmition_id': 1,
                         'start_date': fields.Date.to_string(self.invoice_date),
                        })
                lines.append(invoice_temps)
        return {
            'lines': lines,
            'tax_totals_info': tax_totals_info,
            'with_holding_tax_total': with_holding_tax_total
        }

    def get_endoint(self):
        for rec in self:
            company = rec.get_parent_company()
            ei_type_document = rec.ei_type_document
            if ei_type_document == 'invoice':
                return company.get_endpoint('InvoiceSynchronous')
            elif ei_type_document == 'export_invoice':
                return company.get_endpoint('ExportInvoiceSynchronous')
            elif ei_type_document == 'credit_note':
                return company.get_endpoint('CreditNoteSynchronous')
            elif ei_type_document == 'debit_note':
                return company.get_endpoint('DebitNoteSynchronous')
            elif ei_type_document == 'doc_support':
                return company.get_endpoint('DocumentSupportSynchronous')
            elif ei_type_document == 'note_support':
                return company.get_endpoint('NoteDocumentSupportSynchronous')
            elif ei_type_document == 'payroll':
                return company.get_endpoint('PayrollSynchronous')
            elif ei_type_document == 'payroll_adjustment':
                return company.get_endpoint('PayrollAdjustmentSynchronous')

    def get_ei_uuid(self, response_data):
        ei_uuid = False
        if response_data.get('cufe', False):
            ei_uuid = response_data.get('cufe', False)
        elif response_data.get('cude', False):
            ei_uuid = response_data.get('cude', False)
        elif response_data.get('cuds', False):
            ei_uuid = response_data.get('cuds', False)
        elif response_data.get('cune', False):
            ei_uuid = response_data.get('cune', False)
        return ei_uuid

    def qr_image(self):
        for reccord in self:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=2,
                border=2,
            )
            qr.add_data(reccord.ei_qr_data)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            reccord.ei_qr_image = qr_image

    def send_event(self):
        company = self.get_parent_company()
        for record in self:
            if record.ei_uuid:
                payload = {
                    'event_id': record.ei_type_event,
                    'document_reference': {
                        'cufe': record.ei_uuid
                    }
                }

                if record.ei_type_event == '2':
                    payload['type_rejection_id'] = record.ei_type_rejection

                json_payload = json.dumps(payload)
                get_endpoint = company.get_endpoint('SendEventData')
                url = company.format_url(company.ip_domain,get_endpoint)
                headers = company.get_header_bearer()

                _logger.info("######json_payload###### %s", json_payload)
                _logger.info("######URL_Event###### %s", url)
                _logger.info("######headers###### %s", headers)
                _logger.info("######company.api_timeout###### %s", company.api_timeout)

                try:
                    response = requests.post(url, data=json_payload, headers=headers, timeout=company.api_timeout, verify=False)
                    response_data = response.json()
                    message = response_data.get('message')
                    status_code = 99
                    is_valid = False
                    detailed_error_message = ''

                    send_event_status_result = response_data.get('ResponseDian', {}).get('Envelope', {}).get('Body', {}).get('SendEventUpdateStatusResponse', {}).get('SendEventUpdateStatusResult')

                    if send_event_status_result is not None:
                        status_code = send_event_status_result.get('StatusCode')
                        is_valid = send_event_status_result.get('IsValid', '').lower() == "true"

                        error_messages = send_event_status_result.get('ErrorMessage', {}).get('string', [])
                        detailed_error_message = " ".join(error_messages)

                    if not record.request_edi:
                        request_edi = self.env['co.request.edi'].create({
                            'invoice_id': record.id,
                            'status': 'pending',
                        })
                        record.request_edi = request_edi.id
                    self.env['co.log.edi'].create({
                        'request_id': record.request_edi.id,
                        'is_valid': is_valid,
                        'status_code': status_code,
                        'message': message,
                        'error_message': detailed_error_message,
                        'payload': json.dumps(payload, indent=4, sort_keys=True) ,
                        'response': json.dumps(response.json(), indent=4, sort_keys=True)
                    })

                    body_json = {
                        'HTTP': response.status_code,
                        'Codigo de estado': status_code,
                        'Respuesta': message,
                        'Es valido': is_valid,
                    }
                    body_message_post = f"Evento de Factura electrónica enviado a la DIAN. Estado: {json.dumps(body_json, indent=4, sort_keys=True)}"
                    record.message_post(body=body_message_post)

                except requests.exceptions.RequestException as e:
                    _logger.error("Error Event: %s", e)

    def get_parent_company(self):
        self.ensure_one()
        establishment = self.journal_id.edi_establishment_id
        # Si el establecimiento tiene sucursal (compañía hija) y esta tiene padre, retorna el padre
        if establishment and establishment.branch_company_id and establishment.branch_company_id.parent_id:
            return establishment.branch_company_id.parent_id
        # Si no hay sucursal, usa la compañía de la factura
        return self.company_id

    def send_electronic_invoice(self):
        for record in self:
            if record.is_electronic_invoice:
                record.validate_configuration()

                company = self.get_parent_company()
                _logger.info("ip domain: %s", company.ip_domain)
                payload = record.prepare_invoice_payload()
                get_endpoint = record.get_endoint()
                url = company.format_url(company.ip_domain,get_endpoint)
                if record.ei_type_document == 'invoice':
                    if company.environment == 'test' and company.use_test_id and company.test_set_id:
                        url = f"{url}/{company.test_set_id}"
                        print("--------------URL-Async------------",url)
                if record.ei_type_document == 'payroll' or record.ei_type_document == 'payroll_adjustment':
                    if company.payroll_environment == 'test' and company.use_payroll_test_id and company.payroll_test_set_id:
                        url = f"{url}/{company.payroll_test_set_id}"
                        print("--------------URL-Async------------",url)
                headers = company.get_header_bearer()
                if not record.request_edi:
                    request_edi = self.env['co.request.edi'].create({
                        'invoice_id': record.id,
                        'status': 'pending',
                    })
                    record.request_edi = request_edi.id
                json_payload = json.dumps(payload)
                print("######json_payload######",json_payload)
                print("######url######",url)
                print("######headers######",headers)
                print("######company.api_timeout######",company.api_timeout)
                try:
                    response = requests.post(url, data=json_payload, headers=headers, timeout=company.api_timeout, verify=False)
                    response_data = response.json()
                    print("######response_data######",response_data)
                    print("######response######",response.status_code)
                    if response.status_code == 200:

                        send_bill_sync_result = response_data.get('ResponseDian', {}).get('Envelope', {}).get('Body', {}).get('SendBillSyncResponse', {}).get('SendBillSyncResult')
                        if record.ei_type_document == 'payroll' or record.ei_type_document == 'payroll_adjustment':
                            send_bill_sync_result = response_data.get('ResponseDian', {}).get('Envelope', {}).get('Body', {}).get('SendNominaSyncResponse', {}).get('SendNominaSyncResult')

                        send_test_set_async_result = None
                        if (company.environment == 'test' and company.use_test_id and company.test_set_id) or (company.payroll_environment == 'test' and company.use_payroll_test_id and company.payroll_test_set_id):
                            send_test_set_async_result = response_data.get('ResponseDian', {}).get('Envelope', {}).get('Body', {}).get('SendTestSetAsyncResponse', {}).get('SendTestSetAsyncResult')

                        # pdf
                        endpoint_base_pdf = company.get_endpoint('DownloadPdf')
                        base_url = company.format_url(company.ip_domain,endpoint_base_pdf)
                        if record.ei_type_document == 'payroll' or record.ei_type_document == 'payroll_adjustment':
                            name_pdf = response_data.get('urlpayrollpdf', {})
                        else:
                            name_pdf = response_data.get('urlinvoicepdf', {})
                        url_pdf = f"{base_url}/{company.identification_number}/{name_pdf}"
                        print("######url_pdf######", url_pdf)
                        # qr
                        if response_data.get('QRStr', False):
                            record.ei_qr_data = response_data.get('QRStr')
                            record.qr_image()
                        if name_pdf is not None:
                            record.ei_url_pdf = url_pdf
                            record.ei_pdf_filename = name_pdf
                            response_pdf = requests.get(url_pdf, verify=False)
                            if response_pdf.status_code == 200:
                                pdf_data = base64.b64encode(response_pdf.content)
                                record.ei_pdf_binary = pdf_data

                        if send_bill_sync_result is not None:
                            if send_bill_sync_result.get('IsValid') == "true":
                                record.ei_status = 'accepted'
                                record.ei_is_valid = True
                                if self.get_ei_uuid(response_data):
                                    record.ei_uuid = self.get_ei_uuid(response_data)
                                record.ei_message = response_data.get('message', 'Factura enviada con éxito')
                                record.ei_xml_response = send_bill_sync_result.get('XmlBase64Bytes', '')
                                record.ei_zipinvoicexml_filename = record.name + '.zip'
                                response_xml_filename = record.name + '.xml'

                                # Crear ZIP con invoicexml y urlinvoicepdf
                                zip_data, zip_filename = record.create_zip_from_invoice_data(response_data)
                                if zip_data and zip_filename:
                                    record.ei_zipinvoicexml = zip_data
                                    record.ei_zipinvoicexml_filename = zip_filename
                                else:
                                    # Fallback al método anterior si existe zipinvoicexml o zippayrollxml
                                    zip_invoice_xml = response_data.get('zipinvoicexml', False)
                                    if record.ei_type_document == 'payroll' or record.ei_type_document == 'payroll_adjustment':
                                        zip_invoice_xml = response_data.get('zippayrollxml', False)
                                    if zip_invoice_xml:
                                        try:
                                            record.ei_zipinvoicexml = zip_invoice_xml.encode()
                                        except Exception as e:
                                            _logger.error("Error encoding ZIP Invoice XML: %s", e)
                                            record.ei_message = 'Error al procesar XML de factura ZIP'

                                record.request_edi.write({
                                    'status': 'success',
                                    'response_message': record.ei_message,
                                    'response_xml': record.ei_xml_response,
                                    'response_xml_binary':record.ei_xml_response.encode(),
                                    'response_xml_filename':response_xml_filename,
                                })

                                record.status_code = send_bill_sync_result.get('StatusCode')
                            else:
                                if self.get_ei_uuid(response_data):
                                    record.ei_uuid = self.get_ei_uuid(response_data)
                                error_messages = send_bill_sync_result.get('ErrorMessage', {}).get('string', [])
                                detailed_message = " ".join(error_messages)
                                record.ei_status = 'rejected'
                                record.ei_message = response_data.get('message', 'Error al enviar la factura')
                                record.ei_detailed_message = detailed_message
                                record.status_code = send_bill_sync_result.get('StatusCode')
                                record.request_edi.write({
                                    'status': 'error',
                                    'response_message': f"{record.ei_message} - {detailed_message}",
                                })
                        elif send_test_set_async_result is not None:
                            if send_test_set_async_result.get('ZipKey'):
                                zip_key = send_test_set_async_result.get('ZipKey')
                                is_payroll = False
                                if record.ei_type_document == 'payroll' or record.ei_type_document == 'payroll_adjustment':
                                    is_payroll = True
                                    if record.ei_type_document == 'payroll_adjustment':
                                        time.sleep(5)
                                if self.get_ei_uuid(response_data):
                                    record.ei_uuid = self.get_ei_uuid(response_data)
                                self.get_status_zip(zip_key, is_payroll)
                        else:
                            record.ei_status = 'rejected'
                            record.ei_message = 'Estructura de respuesta inesperada: falta SendBillSyncResult'
                            if response_data.get('message'):
                                record.ei_message = response_data.get('message',False)
                            record.request_edi.write({'status': 'error', 'response_message': record.ei_message})
                    else:
                        record.ei_status = 'rejected'
                        record.ei_message = f"Error en la solicitud API: {response.status_code} - {response.reason}"
                        record.request_edi.write({'status': 'error', 'response_message': record.ei_message})

                    # Crear registro de log
                    self.env['co.log.edi'].create({
                        'request_id': record.request_edi.id,
                        'is_valid': record.ei_is_valid,
                        'status_code': record.status_code,
                        'message': record.ei_message,
                        'error_message': record.ei_detailed_message,
                        'payload': json.dumps(payload, indent=4, sort_keys=True) ,
                        'response': json.dumps(response.json(), indent=4, sort_keys=True),
                    })
                    body_json = {
                        'Codigo de estado': record.status_code,
                        'Respuesta': record.ei_message,
                        'Mensaje detallado': record.ei_detailed_message,
                        'Es valido': record.ei_is_valid,
                    }

                    body_mesaage_post = f"Factura electrónica enviada a la DIAN. Estado: {json.dumps(body_json, indent=4, sort_keys=True)}"
                    record.message_post(body=body_mesaage_post)

                except requests.exceptions.RequestException as e:
                    print("######Error######",str(e))
                    record.ei_status = 'rejected'
                    record.ei_message = f"Error en la solicitud API: {str(e)}"
                    request_edi.write({
                        'status': 'error',
                        'response_message': record.ei_message,
                        'payload': json.dumps(payload, indent=4, sort_keys=True),
                    })
                    raise UserError(record.ei_message)

    def action_document_invoice_check(self):
        for record in self:
            if record.is_electronic_invoice:
                if not record.ei_uuid:
                    raise UserError(_("La factura no Tiene UUID"))
                company = record.get_parent_company()
                endpoint = company.get_endpoint('DocumentStatus')
                base_url = company.format_url(company.ip_domain, endpoint)
                if not base_url.endswith('/'):
                    base_url += '/'
                ei_uuid = record.ei_uuid.lstrip('/')
                get_url = urljoin(base_url, ei_uuid)
                payload = {
                    "sendmail": False,
                    "sendmailtome": False
                }
                headers = company.get_header_bearer()
                try:
                    response = requests.post(get_url, data=json.dumps(payload), headers=headers, timeout=company.api_timeout, verify=False)
                    response_data = response.json()
                    # print("######response_data######",response_data)
                    if response.status_code == 200:
                        send_bill_sync_result = response_data.get('ResponseDian', {}).get('Envelope', {}).get('Body', {}).get('GetStatusResponse', {}).get('GetStatusResult', {})
                        if send_bill_sync_result is not None:
                            if send_bill_sync_result.get('IsValid') == "true":
                                record.ei_is_valid = True
                                record.ei_status = 'accepted' if record.ei_is_valid else 'rejected'
                                record.ei_message = response_data.get('message', 'Factura enviada con éxito' if record.ei_is_valid else 'Error en el envío de la factura')
                                record.ei_xml_response = send_bill_sync_result.get('XmlBase64Bytes', '')
                                response_xml_filename = record.name + '.xml'
                                record.request_edi.write({
                                    'status': 'success' if record.ei_is_valid else 'error',
                                    'response_message': record.ei_message,
                                    'response_xml': record.ei_xml_response,
                                })
                                record.request_edi.write({
                                    'status': 'success',
                                    'response_message': record.ei_message,
                                    'response_xml': record.ei_xml_response,
                                    'response_xml_binary':record.ei_xml_response.encode(),
                                    'response_xml_filename':response_xml_filename,
                                })
                                record.status_code = send_bill_sync_result.get('StatusCode')
                        else:
                            _logger.error("SendBillSyncResult not found in the response.")
                            record.ei_message = 'Error en la respuesta de la DIAN'
                            record.request_edi.write({
                                'status': 'error',
                                'response_message': record.ei_message,
                            })
                    else:
                        record.ei_status = 'rejected'
                        record.ei_message = f"Error en la solicitud API: {response.status_code} - {response.reason}"
                        record.request_edi.write({'status': 'error', 'response_message': record.ei_message})
                    self.env['co.log.edi'].create({
                        'request_id': record.request_edi.id,
                        'is_valid': record.ei_is_valid,
                        'status_code': record.status_code,
                        'message': record.ei_message,
                        'error_message': record.ei_detailed_message,
                        'payload': json.dumps(payload, indent=4, sort_keys=True),
                        'response': json.dumps(response.json(), indent=4, sort_keys=True),
                    })
                    body_json = {
                            'Codifo de estado': record.status_code,
                            'respuesta': record.ei_message,
                            'Es Valido': record.ei_is_valid,
                        }

                    body_mesaage_post = f"Consulta de Factura electrónica a la DIAN. Estado: {json.dumps(body_json, indent=4, sort_keys=True)}"
                    record.message_post(body=body_mesaage_post)
                except requests.exceptions.RequestException as e:
                    record.ei_status = 'rejected'
                    record.ei_message = f"Error en la solicitud API: {str(e)}"
                    record.request_edi.write({'status': 'error', 'response_message': record.ei_message})
                    raise UserError(record.ei_message)
            else:
                raise UserError(_("Este tipo de documento no necesita ser enviado a la DIAN"))

    def get_document_zip(self):
        for record in self:
            if record.is_electronic_invoice:
                if not record.ei_uuid:
                    raise UserError(_("La factura no Tiene UUID"))
                company = record.get_parent_company()
                endpoint = company.get_endpoint('DocumentStatusZip')
                base_url = company.format_url(company.ip_domain, endpoint)
                if not base_url.endswith('/'):
                    base_url += '/'
                ei_uuid = record.ei_uuid.lstrip('/')
                get_url = urljoin(base_url, ei_uuid)
                payload = {
                    "sendmail": False,
                    "sendmailtome": False,
                    "is_payroll": False,
                    "is_eqdoc": True
                }
                headers = company.get_header_bearer()
                try:
                    response = requests.post(get_url, data=json.dumps(payload), headers=headers, timeout=company.api_timeout, verify=False)
                    response_data = response.json()
                    print("######response_data######",response_data)
                    if response.status_code == 200:
                        send_bill_sync_result = response_data.get('ResponseDian', {}).get('Envelope', {}).get('Body', {}).get('GetStatusResponse', {}).get('GetStatusResult', {})

                        if send_bill_sync_result:
                            record.ei_is_valid = send_bill_sync_result.get('IsValid') == "true"
                            record.ei_status = 'accepted' if record.ei_is_valid else 'rejected'
                            record.ei_message = response_data.get('message', 'Factura enviada con éxito' if record.ei_is_valid else 'Error en el envío de la factura')
                            record.ei_xml_response = send_bill_sync_result.get('XmlBase64Bytes', '')
                            response_xml_filename = record.name + '.xml'

                            record.request_edi.write({
                                'status': 'success' if record.ei_is_valid else 'error',
                                'response_message': record.ei_message,
                                'response_xml': record.ei_xml_response,
                                'response_xml_binary': record.ei_xml_response.encode(),
                                'response_xml_filename': response_xml_filename,
                            })

                            # Crear ZIP con invoicexml y urlinvoicepdf
                            zip_data, zip_filename = record.create_zip_from_invoice_data(response_data)
                            if zip_data and zip_filename:
                                record.ei_zipinvoicexml = zip_data
                                record.ei_zipinvoicexml_filename = zip_filename
                            else:
                                _logger.error("No se pudo crear el ZIP con invoicexml y urlinvoicepdf.")

                            record.status_code = send_bill_sync_result.get('StatusCode')
                        else:
                            _logger.error("SendBillSyncResult not found in the response.")
                            record.ei_message = 'Error en la respuesta de la DIAN'
                            record.request_edi.write({
                                'status': 'error',
                                'response_message': record.ei_message,
                            })
                    else:
                        record.ei_status = 'rejected'
                        record.ei_message = f"Error en la solicitud API: {response.status_code} - {response.reason}"
                        record.request_edi.write({'status': 'error', 'response_message': record.ei_message})

                    self.env['co.log.edi'].create({
                        'request_id': record.request_edi.id,
                        'is_valid': record.ei_is_valid,
                        'status_code': record.status_code,
                        'message': record.ei_message,
                        'error_message': record.ei_detailed_message,
                        'payload': json.dumps(payload, indent=4, sort_keys=True),
                        'response': json.dumps(response.json(), indent=4, sort_keys=True),
                    })

                    body_json = {
                        'Codigo de estado': record.status_code,
                        'respuesta': record.ei_message,
                        'Es Valido': record.ei_is_valid,
                    }

                    body_message_post = f"Consulta de Factura electrónica a la DIAN. Estado: {json.dumps(body_json, indent=4, sort_keys=True)}"
                    record.message_post(body=body_message_post)
                except requests.exceptions.RequestException as e:
                    record.ei_status = 'rejected'
                    record.ei_message = f"Error en la solicitud API: {str(e)}"
                    record.request_edi.write({'status': 'error', 'response_message': record.ei_message})
                    raise UserError(record.ei_message)
            else:
                raise UserError(_("Este tipo de documento no necesita ser enviado a la DIAN"))

    def get_status_zip(self, zip_key, is_payroll=False):
        for record in self:
            if record.is_electronic_invoice:
                company = record.get_parent_company()
                endpoint = company.get_endpoint('DocumentStatusZip')
                base_url = company.format_url(company.ip_domain, endpoint)
                url = f"{base_url}/{zip_key}"
                payload = {
                    "sendmail": False,
                    "sendmailtome": False,
                    "is_payroll": is_payroll
                }
                headers = company.get_header_bearer()

                print("######GET STATUS ZIP######")
                print("######json_payload######", payload)
                print("######url######", url)
                print("######headers######", headers)
                try:
                    response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=company.api_timeout, verify=False)
                    print("######response######", response.json())
                    if response.status_code == 200:
                        response_data = response.json()
                        send_status_zip_result = response_data.get('ResponseDian', {}).get('Envelope', {}).get('Body', {}).get('GetStatusZipResponse', {}).get('GetStatusZipResult', {}).get('DianResponse', {})

                        if send_status_zip_result:
                            record.ei_is_valid = send_status_zip_result.get('IsValid') == "true"
                            record.ei_status = 'accepted' if record.ei_is_valid else 'rejected'
                            record.ei_message = response_data.get('message', 'Factura enviada con éxito' if record.ei_is_valid else 'Error en el envío de la factura')
                            record.ei_xml_response = send_status_zip_result.get('XmlBase64Bytes', '')
                            if isinstance(record.ei_xml_response, str):
                                try:
                                    base64.b64decode(record.ei_xml_response)
                                    response_xml_binary = record.ei_xml_response.encode()
                                except Exception as e:
                                    response_xml_binary = b''
                            response_xml_filename = record.name + '.xml'
                            record.request_edi.write({
                                'status': 'success' if record.ei_is_valid else 'error',
                                'response_message': record.ei_message,
                                'response_xml': record.ei_xml_response,
                                'response_xml_binary': response_xml_binary,
                                'response_xml_filename': response_xml_filename,
                            })

                            # Crear ZIP con invoicexml y urlinvoicepdf
                            zip_data, zip_filename = record.create_zip_from_invoice_data(response_data)
                            if zip_data and zip_filename:
                                record.ei_zipinvoicexml = zip_data
                                record.ei_zipinvoicexml_filename = zip_filename
                            else:
                                # Fallback al método anterior si existe zipinvoicexml
                                if 'zipinvoicexml' in response_data:
                                    record.ei_zipinvoicexml = base64.b64encode(response_data['zipinvoicexml'].encode())
                                else:
                                    _logger.error("No se pudo crear ZIP ni encontrar zipinvoicexml en la respuesta.")

                            record.status_code = send_status_zip_result.get('StatusCode')
                        else:
                            _logger.error("SendBillSyncResult not found in the response.")
                            record.ei_message = 'Error en la respuesta de la DIAN'
                            record.request_edi.write({
                                'status': 'error',
                                'response_message': record.ei_message,
                            })
                    else:
                        record.ei_status = 'rejected'
                        record.ei_message = f"Error en la solicitud API: {response.status_code} - {response.reason}"
                        record.request_edi.write({'status': 'error', 'response_message': record.ei_message})

                    self.env['co.log.edi'].create({
                        'request_id': record.request_edi.id,
                        'is_valid': record.ei_is_valid,
                        'status_code': record.status_code,
                        'message': record.ei_message,
                        'error_message': record.ei_detailed_message,
                        'payload': json.dumps(payload, indent=4, sort_keys=True),
                        'response': json.dumps(response.json(), indent=4, sort_keys=True),
                    })

                    body_json = {
                        'Codigo de estado': record.status_code,
                        'respuesta': record.ei_message,
                        'Es Valido': record.ei_is_valid,
                    }

                    body_message_post = f"Consulta de Factura electrónica a la DIAN. Estado: {json.dumps(body_json, indent=4, sort_keys=True)}"
                    record.message_post(body=body_message_post)
                except requests.exceptions.RequestException as e:
                    record.ei_status = 'rejected'
                    record.ei_message = f"Error en la solicitud API: {str(e)}"
                    record.request_edi.write({'status': 'error', 'response_message': record.ei_message})
                    raise UserError(record.ei_message)
            else:
                raise UserError(_("Este tipo de documento no necesita ser enviado a la DIAN"))

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Cuando se cambia el diario, ajusta el tipo de movimiento basado en el tipo de documento del diario."""
        for rec in self:
            if rec.journal_id and rec.journal_id.resolution_type_document_id:
                doc_code = rec.journal_id.resolution_type_document_id.code
                if doc_code == '91':  # Nota de crédito
                    rec.move_type = 'out_refund'
                elif doc_code == '92':  # Nota de débito
                    rec.move_type = 'out_invoice'
                    # Aquí podrías agregar un indicador o campo adicional para marcar que es nota de débito
                elif doc_code in ('01', '02'):  # Facturas normales
                    rec.move_type = 'out_invoice'

    def action_print_export_invoice(self):
        """Print the export invoice report."""
        self.ensure_one()
        return self.env.ref('l10n_co_edi_electronic_invoice.report_export_invoice').report_action(self)

    @api.depends('partner_shipping_id', 'partner_id')
    def _compute_export_destination(self):
        for move in self:
            destination = False

            # Use shipping address if available
            partner = move.partner_shipping_id if move.partner_shipping_id else move.partner_id

            if partner:
                # Build the destination string with city/municipality, state, country
                location_parts = []

                # First try to get the city name
                if partner.city:
                    location_parts.append(partner.city)
                # If no city but has municipality_id, use that instead
                elif hasattr(partner, 'municipality_id') and partner.municipality_id:
                    location_parts.append(partner.municipality_id.name)

                if partner.state_id:
                    location_parts.append(partner.state_id.name)

                if partner.country_id:
                    location_parts.append(partner.country_id.name)

                destination = " - ".join([p for p in location_parts if p])

            move.export_destination = destination

    @api.depends('payment_form_id')
    def _compute_export_payment_means(self):
        """Calculate payment means based on payment form"""
        for move in self:
            payment_means = ''
            if move.payment_form_id:
                # Map payment form values to human-readable descriptions for export
                if move.payment_form_id.id == 1:  # Contado
                    payment_means = 'Pago de Contado'
                elif move.payment_form_id.id == 2:  # Crédito
                    payment_means = 'Pago a Crédito'
                else:
                    payment_means = move.payment_form_id.name

            move.export_payment_means = payment_means

    # Add this method to the AccountMove class
    def amount_to_text_custom(self, amount, currency):
        """Convert amount to words using num2words with Spanish language."""
        from num2words import num2words

        # Always use Spanish language for all currencies
        language = 'es'

        # Convert number to words
        try:
            whole_word = num2words(int(amount), lang=language)
            return whole_word
        except NotImplementedError:
            # Fallback if language not supported
            return num2words(int(amount), lang='en')
        except Exception:
            # General fallback
            return str(int(amount))

    def get_currency_name_in_words(self, currency_code):
        """Get the currency name in plural form based on currency code."""
        currency_names = {
            'USD': 'DÓLARES',
            'EUR': 'EUROS',
            'GBP': 'LIBRAS ESTERLINAS',
            'CAD': 'DÓLARES CANADIENSES',
            'AUD': 'DÓLARES AUSTRALIANOS',
            'JPY': 'YENES',
            'CHF': 'FRANCOS SUIZOS',
            'CNY': 'YUANES',
            'MXN': 'PESOS MEXICANOS',
            'BRL': 'REALES BRASILEÑOS',
            'ARS': 'PESOS ARGENTINOS',
            'CLP': 'PESOS CHILENOS',
            'PEN': 'SOLES',
            'BOB': 'BOLIVIANOS',
        }
        return currency_names.get(currency_code, currency_code)

    def action_send_electronic_invoice_mass(self):
        """
        Acción masiva para enviar facturas electrónicas seleccionadas al API.
        Solo procesa las que tengan is_electronic_invoice=True.
        """
        for record in self:
            if record.is_electronic_invoice:
                record.send_electronic_invoice()

    def create_zip_from_invoice_data(self, response_data):
        """
        Crea un archivo ZIP con el XML de la factura y el PDF desde la respuesta de la API.
        """
        self.ensure_one()
        try:
            # Obtener los datos de la respuesta
            invoice_xml = response_data.get('invoicexml', '')
            url_invoice_pdf = response_data.get('urlinvoicepdf', '')

            if not invoice_xml:
                _logger.warning("invoicexml no encontrado en la respuesta")
                return None, None

            # Crear un buffer para el ZIP
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Agregar el XML al ZIP
                xml_filename = f"{self.ei_number or 'invoice'}.xml"
                if isinstance(invoice_xml, str):
                    # Si invoicexml viene como string base64, decodificarlo
                    try:
                        xml_data = base64.b64decode(invoice_xml)
                    except Exception:
                        # Si no es base64, usar como string directo
                        xml_data = invoice_xml.encode('utf-8')
                else:
                    xml_data = invoice_xml

                zip_file.writestr(xml_filename, xml_data)

                # Descargar y agregar el PDF al ZIP si existe la URL
                if url_invoice_pdf:
                    try:
                        # Construir la URL completa del PDF
                        endpoint_base_pdf = self.company_id.get_endpoint('DownloadPdf')
                        base_url = self.company_id.format_url(self.company_id.ip_domain, endpoint_base_pdf)
                        pdf_url = f"{base_url}/{self.company_id.identification_number}/{url_invoice_pdf}"

                        # Descargar el PDF
                        pdf_response = requests.get(pdf_url, verify=False, timeout=self.company_id.api_timeout)
                        if pdf_response.status_code == 200:
                            pdf_filename = f"{self.ei_number or 'invoice'}.pdf"
                            zip_file.writestr(pdf_filename, pdf_response.content)
                        else:
                            _logger.warning(f"No se pudo descargar el PDF desde {pdf_url}: {pdf_response.status_code}")
                    except Exception as e:
                        _logger.error(f"Error al descargar y agregar PDF al ZIP: {str(e)}")

            # Obtener el contenido del ZIP y codificarlo en base64
            zip_content = zip_buffer.getvalue()
            zip_base64 = base64.b64encode(zip_content)
            zip_filename = f"{self.ei_number or 'invoice'}.zip"

            return zip_base64, zip_filename

        except Exception as e:
            _logger.error(f"Error al crear ZIP desde datos de factura: {str(e)}")
            return None, None
