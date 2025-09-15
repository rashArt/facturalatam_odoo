/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class PopupLoading extends AbstractAwaitablePopup {
    static template = "l10n_co_edi_electronic_invoice.PopupLoading";
    static defaultProps = {
        title: "Cargando...",
        body: "Por favor espere.",
        confirmText: "Enviando...",
        countdown: 30,
    };
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({
            title: this.props.title || "Cargando...",
            body: this.props.body || "Por favor espere.",
            confirmText: this.props.confirmText || "Enviando...",
            countdown: this.props.countdown,
        });
        this.close = this.props.close;
        this.send();
        this.interval = setInterval(() => {
            if (this.state.countdown > 0) {
                this.state.countdown -= 1;
            } else {
                clearInterval(this.interval);
            }
        }, 1000);
    }

    async send() {
        try {
            const result = await this.env.services.orm.call(
                "pos.order",
                "get_account_move",
                [this.props.orderId]
            );
            this.state.title = "Factura Enviada";
            this.state.body = "La operación se completó correctamente.";
            this.state.confirmText = "Recibiendo.";
            this.props.close({ payload: result });
        } catch (error) {
            this.state.title = "Error de envio";
            this.state.body = "Hubo un problema al procesar la solicitud.";
            this.state.confirmText = "Continuar";
            this.props.close({ payload: null });
            throw error; // Manejo de errores
        }
    }

    willUnmount() {
        super.willUnmount();
        clearInterval(this.interval); // Limpia el intervalo al cerrar el popup
    }
}
