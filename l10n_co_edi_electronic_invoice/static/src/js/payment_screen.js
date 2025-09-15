/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useService } from "@web/core/utils/hooks";
import { PopupLoading } from "@l10n_co_edi_electronic_invoice/js/popup_loading";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.popup = useService("popup");
    },
    async afterOrderValidation(suggestToSync = true) {
        const isToInvoice = this.currentOrder.is_to_invoice();
        console.log('Es una factura electrónica?:', isToInvoice);
        if(isToInvoice) {
            const orderId = this.currentOrder.server_id;
            if (orderId) {
                const { payload } = await this.popup.add(PopupLoading, {
                    title: "Enviando Factura Electrónica",
                    body: "Por favor espere mientras se procesa la factura.",
                    orderId,
                });
                if (payload) {
                    console.log(this.currentOrder.pos);
                    let journals = this.currentOrder.pos.journals;
                    let journal = journals.find(j => j.id == this.currentOrder.pos.config.invoice_journal_id[0]);
                    this.currentOrder.journal = journal;
                    this.currentOrder.account_move = payload;
                }
            }
        }
        await super.afterOrderValidation(...arguments);
    }
});