/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";

patch(PartnerDetailsEdit.prototype, {
    setup(){
        super.setup(...arguments);
        this.intFields.push(
            'l10n_co_edi_type_document_identification_id',
            'identification_co_number',
            'municipality_id',
            'l10n_co_edi_merchant_registration',
            'l10n_co_edi_type_organization_id',
            'l10n_co_edi_type_liability_id',
            'type_regime_id',
        );
        const partner = this.props.partner;
        this.changes.l10n_co_edi_type_document_identification_id = partner.l10n_co_edi_type_document_identification_id && partner.l10n_co_edi_type_document_identification_id[0]
        this.changes.identification_co_number = partner.identification_co_number && partner.identification_co_number
        this.changes.municipality_id = partner.municipality_id && partner.municipality_id[0]
        this.changes.l10n_co_edi_merchant_registration = partner.l10n_co_edi_merchant_registration && partner.l10n_co_edi_merchant_registration
        this.changes.l10n_co_edi_type_organization_id = partner.l10n_co_edi_type_organization_id && partner.l10n_co_edi_type_organization_id[0]
        this.changes.l10n_co_edi_type_liability_id = partner.l10n_co_edi_type_liability_id && partner.l10n_co_edi_type_liability_id[0]
        this.changes.type_regime_id = partner.type_regime_id && partner.type_regime_id[0]
    },
});