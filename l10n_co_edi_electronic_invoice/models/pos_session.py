# -*- coding: utf-8 -*-

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _pos_ui_models_to_load(self):
        result = super(PosSession, self)._pos_ui_models_to_load()
        result.append('l10n_co_fl.type_document_identification')
        result.append('l10n_co_fl.municipality')
        result.append('l10n_co_fl.type.organization')
        result.append('l10n_co_fl.type.liability')
        result.append('l10n_co_fl.type.regime')
        result.append('account.journal')
        result.append('res.company')
        return result

    # fields custom for res.parnert
    def _loader_params_res_partner(self):
        result = super(PosSession, self)._loader_params_res_partner()
        result["search_params"]["fields"].extend([
            'l10n_co_edi_type_document_identification_id',
            'identification_co_number',
            'municipality_id',
            'l10n_co_edi_merchant_registration',
            'l10n_co_edi_type_organization_id',
            'l10n_co_edi_type_liability_id',
            'type_regime_id'
        ])
        return result

    # fields from model l10n_co_fl.type_document_identification
    def _loader_params_l10n_co_fl_type_document_identification(self):
        return {
            'search_params': {
                'fields': ['name', 'code'],
            },
        }

    def _loader_params_l10n_co_fl_municipality(self):
        return {
            'search_params': {
                'fields': ['name', 'code'],
            },
        }

    def _loader_params_l10n_co_fl_type_organization(self):
        return {
            'search_params': {
                'fields': ['name', 'code'],
            },
        }

    def _loader_params_l10n_co_fl_type_liability(self):
        return {
            'search_params': {
                'fields': ['name', 'code'],
            },
        }

    def _loader_params_l10n_co_fl_type_regime(self):
        return {
            'search_params': {
                'fields': ['name', 'code'],
            },
        }

    def _loader_params_account_journal(self):
        return {
            'search_params': {
                'fields': [
                    'resolution',
                    'name',
                    'type',
                    'resolution_date',
                    'from_number',
                    'to_number',
                    'date_from',
                    'date_to',
                    'technical_key'
                ],
            },
        }

    # load model into pos
    def _get_pos_ui_l10n_co_fl_type_document_identification(self, params):
        return self.env['l10n_co_fl.type_document_identification'].search_read(**params['search_params'])

    def _get_pos_ui_l10n_co_fl_municipality(self, params):
        return self.env['l10n_co_fl.municipality'].search_read(**params['search_params'])

    def _get_pos_ui_l10n_co_fl_type_organization(self, params):
        return self.env['l10n_co_fl.type.organization'].search_read(**params['search_params'])

    def _get_pos_ui_l10n_co_fl_type_liability(self, params):
        return self.env['l10n_co_fl.type.liability'].search_read(**params['search_params'])

    def _get_pos_ui_l10n_co_fl_type_regime(self, params):
        return self.env['l10n_co_fl.type.regime'].search_read(**params['search_params'])

    def _get_pos_ui_account_journal(self, params):
        return self.env['account.journal'].search_read(**params['search_params'])

    @api.model
    def _loader_params_res_company(self):
        """ Agregamos los campos personalizados de la compañía que queremos cargar en el POS """
        params = super()._loader_params_res_company()
        params['search_params']['fields'].extend([
            'business_name',
            'merchant_registration',
            'address',
            'use_api_mail_server',
            'type_document_identification_id',
            'type_organization_id',
            'type_regime_id',
            'type_liability_id',
            'municipality_id',
            'identification_number',
        ])
        return params
