/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.notificationService = useService("notification");
        this.state = useState({
            showDialog: false, // Estado inicial del diálogo
        });
    },
    async afterOrderValidation() {
        const isToInvoice = this.currentOrder.is_to_invoice();
        console.log('Es una factura electrónica?:', isToInvoice);
        if(isToInvoice) {
            const orderId = this.currentOrder.id;
            if (orderId) {
                // this.notificationService.add(
                //     "Enviando Factura al servicio... ",
                //     { autocloseDelay: 3000, title: "Cargando...", type: "info" }
                // );
                this.openDialog()
                const result = await this.env.services.orm.call(
                    "pos.order",
                    "get_account_move",
                    [orderId]
                );
                this.closeDialog()
                this.currentOrder.account_move = result;
                console.log("Resultado de la API:", result);
            }
        }
        await super.afterOrderValidation(...arguments);
    },
    openDialog() {
        this.state.showDialog = true; // Cambiar el estado para mostrar el diálogo
    },
    closeDialog() {
        this.state.showDialog = false; // Cambiar el estado para ocultar el diálogo
    }
});