/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";


class BarcodeOrderScanner {

    constructor(env) {
        this.env = env;
        this.buffer = "";
        this.timer = null;
    }


    start() {

        document.addEventListener(
            "keydown",
            this._onKeyDown.bind(this),
            true
        );

        console.log(
            "Barcode Order Scanner Started"
        );
    }



    _onKeyDown(event) {

        if (event.key === "Enter") {


            if (this.buffer.length > 2) {


                const barcode = this.buffer;


                console.log(
                    "Scanned Barcode:",
                    barcode
                );


                this.processBarcode(barcode);

            }


            this.buffer = "";

            return;
        }



        if (event.key.length === 1) {

            this.buffer += event.key;

        }



        clearTimeout(this.timer);



        this.timer = setTimeout(() => {

            this.buffer = "";

        }, 150);

    }





    async processBarcode(barcode) {


        const controller =
            this.env.services.action.currentController;



        if (!controller) {

            console.log(
                "Controller not found"
            );

            return;
        }





        const resModel =
            controller.action.res_model;



        console.log(
            "MODEL NAME:",
            resModel
        );




        if (
            resModel !== "sale.order" &&
            resModel !== "purchase.order" &&
            resModel !== "stock.picking"
        ) {

            console.log(
                "Not Sale/Purchase"
            );

            return;
        }





        const orderId =
            controller.currentState.resId;



        console.log(
            "ORDER ID:",
            orderId
        );





        if (!orderId) {


            console.log(
                "Please save order first"
            );


            return;

        }






        const result = await rpc(
            "/barcode_order_scan/add",
            {
                model: resModel,
                order_id: orderId,
                barcode: barcode,
            }
        );





        console.log(
            "RPC RESULT:",
            result
        );





        if (!result) {


            console.log(
                "Product not found"
            );


            return;

        }





        console.log(
            "Product Added:",
            result.name
        );





        /*
            Update Odoo form without browser refresh
        */


        const formController =
            window.barcodeFormController;


        console.log(
            "FORM CONTROLLER",
            formController
        );


        const record =
            formController?.model?.root;


        console.log(
            "BARCODE ROOT RECORD",
            record
        );




        if (record) {


            try {


                await record.load();


                console.log(
                    "Form updated"
                );


            } catch (error) {


                console.log(
                    "Record reload failed",
                    error
                );

            }

        }



    }

}





registry.category("services").add(
    "barcode_order_scanner",
    {

        start(env) {


            const scanner =
                new BarcodeOrderScanner(env);


            scanner.start();


            return scanner;

        },

    }
);