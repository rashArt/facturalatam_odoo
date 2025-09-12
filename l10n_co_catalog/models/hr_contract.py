# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Employee Contract'

    TYPE_WORKER_SELECTION = [
        ('1', 'Dependiente'),
        ('2', 'Servicio domestico'),
        ('3', 'Madre comunitaria'),
        ('4', 'Aprendices del Sena en etapa lectiva'),
        ('5', 'Funcionarios públicos sin tope máximo de IBC'),
        ('6', 'Aprendices del SENA en etapa productiva'),
        ('7', 'Estudiantes de postgrado en salud'),
        ('8', 'Profesor de establecimiento particular'),
        ('9', 'Estudiantes aportes solo riesgos laborales'),
        ('10', 'Dependiente entidades o universidades públicas con régimen especial en salud'),
        ('11', 'Cooperados o pre cooperativas de trabajo asociado'),
        ('12', 'Trabajador dependiente de entidad beneficiaria del sistema general de participaciones - aportes patronales'),
        ('13', 'Trabajador de tiempo parcial'),
        ('14', 'Pre pensionado de entidad en liquidación'),
        ('15', 'Pre pensionado con aporte voluntario a salud'),
        ('16', 'Estudiantes de prácticas laborales en el sector público'),
    ]

    SUB_TYPE_WORKER_SELECTION = [
        ('1', 'No Aplica'),
        ('2', 'Dependiente pensionado por vejez activo'),
        ('3', 'Independiente pensionado por vejez activo'),
        ('4', 'Cotizante no obligado a cotizar a pensión por edad'),
        ('5', 'Cotizante con requisitos cumplidos para pensión'),
        ('6', 'Cotizante a quien se le ha reconocido indemnización sustitutiva o devolución de saldos'),
        ('7', 'Cotizante perteneciente a un régimen exceptuado de pensiones'),
        ('8', 'Cotizante pensionado con mesada superior a 25 SMLMV'),
        ('9', 'Residente en el exterior afiliado voluntario al sistema general de pensiones y/o afiliado'),
        ('10', 'Conductores del servicio público de transporte terrestre automotor individual de pasajeros en vehículos taxi Decreto 1047 de 2014'),
        ('11', 'Conductores servicio taxi no aporte pensión Dec. 1047'),
    ]

    ei_schedule_pay = fields.Selection([
        ('1', 'Semanal'),
        ('4', 'Quincenal'),
        ('5', 'Mensual'),
    ], string='Periodo de Nómina Electrónica', compute='_compute_ei_schedule_pay', store=True, help="El API no sopporta todos los tipos de periodos, seleccione el más acorde")

    ei_contract_type_id = fields.Selection(related="contract_type_id.ei_contract_type_id", string="Tipo de Contrato de Nómina Electrónica", store=True, readonly=True, help="El tipo de contrato debe contener el valor en campo equivalente")

    ei_type_worker_id = fields.Selection(
        selection=TYPE_WORKER_SELECTION,
        string="Tipo de empleado",
        required=True
    )
    ei_sub_type_worker_id = fields.Selection(
        selection=SUB_TYPE_WORKER_SELECTION,
        string="Subtipo de empleado",
        required=True
    )

    @api.depends('schedule_pay')
    def _compute_ei_schedule_pay(self):
        mapping = {
            'weekly': '1',
            'bi-weekly': '4',
            'monthly': '5',
        }
        for record in self:
            record.ei_schedule_pay = mapping.get(record.schedule_pay) or ''
