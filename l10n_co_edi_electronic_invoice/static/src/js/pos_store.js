/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    // @Override
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.document_identifications = loadedData['l10n_co_fl.type_document_identification'];
        // console.log(this.document_identifications);
        this.municipalities = loadedData['l10n_co_fl.municipality'];
        // console.log(this.municipalities);
        this.organizations = loadedData['l10n_co_fl.type.organization'];
        // console.log(this.organizations);
        this.liabilities = loadedData['l10n_co_fl.type.liability'];
        // console.log(this.liabilities);
        this.regimes = loadedData['l10n_co_fl.type.regime'];
        // console.log(this.regimes);
        this.journals = loadedData['account.journal'];
    },
    getReceiptHeaderData(order) {
        const result = super.getReceiptHeaderData(...arguments);
        if (order && this.company?.country?.code === "CO") {
            result.account_move = order.account_move;
            result.journal = order.journal;
            result.partner = order.partner;
        }
        console.log('getReceiptHeaderData', result)
        return result;
    },
});
