/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";


patch(FormController.prototype, {

    setup() {

        super.setup(...arguments);

        window.barcodeFormController = this;

        console.log(
            "Barcode Controller Stored",
            this
        );

        console.log(
            "Barcode Model",
            this.model
        );

    },

});