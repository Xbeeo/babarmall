/** @odoo-module **/

import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

const SUPPORTED_MODELS = ["sale.order", "purchase.order", "stock.picking"];

// Order line rows sirf form view ke andar (search dialog ki rows ignore)
const LINE_SELECTOR = ".o_form_view tr.o_data_row";

// Odoo list cells ke "name" attribute (td[name='...'])
const PRODUCT_CELLS = ["product_id", "product_template_id"];
const QTY_CELLS = ["product_uom_qty", "product_qty", "quantity"];


class BarcodeOrderScanner {

    constructor(env) {

        this.env = env;

        // ---------------- Barcode input ----------------
        this.buffer = "";
        this.timer = null;

        // ---------------- Current barcode scan ----------------
        this.lastScannedProductId = null;
        this.lastScannedLineId = null;
        this.lastProductName = "";
        this.scanSequence = 0;

        // ---------------- Barcode observer ----------------
        this.observer = null;
        this.highlightTimer = null;

        // ---------------- Manual watcher ----------------
        this.manualTimer = null;
        this.manualSnapshot = new Map();
        this.manualWatcherStarted = false;
        this.isManualChecking = false;

        // Barcode ke baad kuch der manual watcher ignore
        this.ignoreManualUntil = 0;

        // Ignore window khatam hone par snapshot dobara lena
        this.needsResnapshot = false;

        // Naya document/record khulne par silent baseline
        this.manualContext = null;
        this.baselineUntil = 0;

        // Last manually highlighted line (data-id)
        this.manualHighlightLineId = null;
    }


    // =====================================================
    // START
    // =====================================================

    start() {

        document.addEventListener(
            "keydown",
            this._onKeyDown.bind(this),
            true
        );

        this.startManualWatcher();

        console.log("Barcode Order Scanner Started");
    }


    // =====================================================
    // CONTROLLER / MODEL
    // =====================================================

    getCurrentController() {

        try {

            if (
                this.env &&
                this.env.services &&
                this.env.services.action
            ) {
                return this.env.services.action.currentController;
            }

        } catch (error) {

            console.log("Controller error:", error);
        }

        return null;
    }


    getCurrentModel() {

        const controller = this.getCurrentController();

        if (!controller) {
            return null;
        }

        return controller.action?.res_model || null;
    }


    isSupportedModel() {

        return SUPPORTED_MODELS.includes(
            this.getCurrentModel()
        );
    }


    // =====================================================
    // BARCODE INPUT
    // =====================================================

    _onKeyDown(event) {

        if (event.key === "Enter") {

            if (this.buffer.length > 2) {

                const barcode = this.buffer.trim();

                console.log("Scanned Barcode:", barcode);

                this.processBarcode(barcode);
            }

            this.buffer = "";

            clearTimeout(this.timer);

            return;
        }

        // Input fields mein manual typing ko barcode na samjha jaye
        const target = event.target;

        if (
            target &&
            (
                target.tagName === "INPUT" ||
                target.tagName === "TEXTAREA" ||
                target.isContentEditable
            )
        ) {
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


    // =====================================================
    // PROCESS BARCODE
    // =====================================================

    async processBarcode(barcode) {

        const controller = this.getCurrentController();

        if (!controller) {

            console.log("No current controller found");

            return;
        }

        const resModel = controller.action?.res_model;

        if (!SUPPORTED_MODELS.includes(resModel)) {

            console.log(
                "Barcode scanner not supported on:",
                resModel
            );

            return;
        }

        const orderId = controller.currentState?.resId;

        if (!orderId) {

            this.showMessage("Please save the document first.");

            return;
        }

        // Scanner ki DOM changes ko manual change na samjha jaye
        this.ignoreManualUntil = Date.now() + 2000;

        let result;

        try {

            result = await rpc(
                "/barcode_order_scan/add",
                {
                    model: resModel,
                    order_id: orderId,
                    barcode: barcode,
                }
            );

        } catch (error) {

            console.error("Barcode RPC Error:", error);

            this.showMessage("Something went wrong while scanning.");

            return;
        }

        console.log("RPC RESULT:", result);

        if (
            !result ||
            result.success === false
        ) {

            this.showMessage(
                result?.message ||
                "Product not found."
            );

            return;
        }

        // ---------------- Save scan ----------------

        this.scanSequence++;

        const sequence = this.scanSequence;

        this.lastScannedProductId =
            result.product_id
                ? String(result.product_id)
                : null;

        this.lastScannedLineId =
            result.line_id
                ? String(result.line_id)
                : null;

        this.lastProductName =
            String(result.name || "").trim();

        console.log(
            "LATEST BARCODE SCAN:",
            {
                scan: sequence,
                lineId: this.lastScannedLineId,
                productId: this.lastScannedProductId,
                product: this.lastProductName,
                quantity: result.quantity,
            }
        );

        this.stopBarcodeObserver();

        // Ab barcode highlight active hai, purani manual highlight hata do
        this.manualHighlightLineId = null;

        // ---------------- Reload Odoo record ----------------

        const formController =
            window.barcodeFormController ||
            controller;

        const record = formController?.model?.root;

        if (record) {

            try {

                await record.load();

                console.log("Form record reloaded");

            } catch (error) {

                console.log("Record reload failed:", error);
            }
        }

        // Reload ke baad bhi thodi der manual watcher ignore,
        // phir naya snapshot lo (checkManualChanges mein)
        this.ignoreManualUntil = Date.now() + 1500;

        this.needsResnapshot = true;

        this.findAndHighlightCurrentLine(
            this.lastScannedLineId,
            this.lastScannedProductId,
            this.lastProductName,
            sequence
        );
    }


    // =====================================================
    // FIND BARCODE LINE
    // =====================================================

    findAndHighlightCurrentLine(
        lineId,
        productId,
        productName,
        sequence
    ) {

        const row = this.findProductRow(
            lineId,
            productId,
            productName
        );

        if (row) {

            this.applyBarcodeHighlight(
                row,
                lineId,
                productId,
                productName,
                sequence
            );

        } else {

            console.log("Barcode row not found immediately.");
        }

        this.startBarcodeObserver(
            lineId,
            productId,
            productName,
            sequence
        );
    }


    findProductRow(
        lineId,
        productId,
        productName
    ) {

        const rows = document.querySelectorAll("tr.o_data_row");

        if (!rows.length) {
            return null;
        }

        // 1. Exact line id
        if (lineId) {

            for (const row of rows) {

                if (this.rowContainsId(row, lineId)) {
                    return row;
                }
            }
        }

        // 2. Product id
        if (productId) {

            for (const row of rows) {

                if (this.rowContainsProductId(row, productId)) {
                    return row;
                }
            }
        }

        // 3. Product name
        const cleanName = this.cleanProductName(productName);

        if (cleanName) {

            for (const row of rows) {

                const rowText = this.normalizeText(
                    row.textContent || ""
                );

                if (rowText.includes(cleanName)) {
                    return row;
                }
            }
        }

        return null;
    }


    rowContainsId(row, lineId) {

        if (!row || !lineId) {
            return false;
        }

        const id = String(lineId);

        if (
            String(row.getAttribute("data-id")) === id ||
            String(row.getAttribute("data-record-id")) === id
        ) {
            return true;
        }

        const elements = row.querySelectorAll(
            "[data-id], [data-record-id]"
        );

        for (const element of elements) {

            if (
                String(element.getAttribute("data-id")) === id ||
                String(element.getAttribute("data-record-id")) === id
            ) {
                return true;
            }
        }

        return false;
    }


    rowContainsProductId(row, productId) {

        if (!row || !productId) {
            return false;
        }

        const id = String(productId);

        if (String(row.getAttribute("data-product-id")) === id) {
            return true;
        }

        const elements = row.querySelectorAll("[data-product-id]");

        for (const element of elements) {

            if (
                String(element.getAttribute("data-product-id")) === id
            ) {
                return true;
            }
        }

        return false;
    }


    cleanProductName(name) {

        if (!name) {
            return "";
        }

        let value = String(name).trim().toLowerCase();

        value = value.replace(/^\[[^\]]+\]\s*/, "");

        return this.normalizeText(value);
    }


    normalizeText(value) {

        return String(value)
            .trim()
            .toLowerCase()
            .replace(/\s+/g, " ");
    }


    // =====================================================
    // BARCODE OBSERVER
    // =====================================================

    startBarcodeObserver(
        lineId,
        productId,
        productName,
        sequence
    ) {

        this.stopBarcodeObserver();

        const currentSequence = sequence;

        this.observer = new MutationObserver(() => {

            if (this.scanSequence !== currentSequence) {

                this.stopBarcodeObserver();

                return;
            }

            const row = this.findProductRow(
                lineId,
                productId,
                productName
            );

            if (!row) {
                return;
            }

            this.applyBarcodeHighlight(
                row,
                lineId,
                productId,
                productName,
                currentSequence
            );
        });

        this.observer.observe(
            document.body,
            {
                childList: true,
                subtree: true,
            }
        );

        clearTimeout(this.highlightTimer);

        this.highlightTimer = setTimeout(() => {

            if (this.scanSequence !== currentSequence) {
                return;
            }

            const row = this.findProductRow(
                lineId,
                productId,
                productName
            );

            if (row) {

                this.applyBarcodeHighlight(
                    row,
                    lineId,
                    productId,
                    productName,
                    currentSequence
                );
            }

        }, 500);
    }


    stopBarcodeObserver() {

        if (this.observer) {

            this.observer.disconnect();

            this.observer = null;
        }

        clearTimeout(this.highlightTimer);

        this.highlightTimer = null;
    }


    applyBarcodeHighlight(
        row,
        lineId,
        productId,
        productName,
        sequence
    ) {

        if (!row) {
            return;
        }

        if (sequence !== this.scanSequence) {
            return;
        }

        this.removeAllHighlights();

        this.highlightRow(row);

        try {

            row.scrollIntoView({
                behavior: "smooth",
                block: "center",
            });

        } catch (error) {

            console.log("Scroll error:", error);
        }
    }


    // =====================================================
    // =====================================================
    // MANUAL WATCHER
    // =====================================================
    // =====================================================

    startManualWatcher() {

        if (this.manualWatcherStarted) {
            return;
        }

        this.manualWatcherStarted = true;

        // MutationObserver nahi, polling: Odoo dropdown/search mein
        // bohat DOM changes hoti hain.
        this.manualTimer = setInterval(() => {

            this.checkManualChanges();

        }, 500);

        console.log("MANUAL WATCHER ACTIVE (500ms)");
    }


    // Har document (model + record id) ki apni baseline
    getContextKey() {

        const controller = this.getCurrentController();

        return (
            this.getCurrentModel() +
            ":" +
            (controller?.currentState?.resId || "new")
        );
    }


    getOrderLineRows() {

        if (!this.isSupportedModel()) {
            return [];
        }

        return Array.from(
            document.querySelectorAll(LINE_SELECTOR)
        );
    }


    // Odoo 17/18: tr.o_data_row ka data-id = "datapoint_XX"
    getRowLineId(row) {

        if (!row) {
            return null;
        }

        return (
            row.getAttribute("data-id") ||
            row.getAttribute("data-record-id") ||
            null
        );
    }


    // -----------------------------------------------------
    // PRODUCT NAME (cell text ya input value)
    //
    // Return: { name, pending }
    // pending = user abhi product search mein type kar raha hai
    // (autocomplete dropdown khula hai), is liye abhi ka value
    // final nahi hai.
    // -----------------------------------------------------

    getRowProduct(row) {

        for (const fieldName of PRODUCT_CELLS) {

            const cell = row.querySelector(
                `td[name='${fieldName}']`
            );

            if (!cell) {
                continue;
            }

            const input = cell.querySelector("input");

            if (input) {

                const typing =
                    document.activeElement === input &&
                    !!document.querySelector(
                        ".o-autocomplete--dropdown-menu"
                    );

                if (typing) {
                    return { name: "", pending: true };
                }

                const name = this.normalizeText(input.value || "");

                if (name) {
                    return { name, pending: false };
                }

                continue;
            }

            const name = this.normalizeText(cell.textContent || "");

            if (name) {
                return { name, pending: false };
            }
        }

        return { name: "", pending: false };
    }


    // -----------------------------------------------------
    // QUANTITY SIGNATURE
    //
    // Sab qty columns (demand / quantity / product_qty) ka
    // combined string, taake koi bhi change detect ho.
    // -----------------------------------------------------

    getRowQuantity(row) {

        const values = [];

        for (const fieldName of QTY_CELLS) {

            const cell = row.querySelector(
                `td[name='${fieldName}']`
            );

            if (!cell) {
                continue;
            }

            const input = cell.querySelector("input");

            const raw = input
                ? input.value
                : cell.textContent;

            const number = parseFloat(
                String(raw || "").replace(/[^0-9.\-]/g, "")
            );

            values.push(
                fieldName + "=" + (isNaN(number) ? "" : number)
            );
        }

        return values.join("|");
    }


    getManualRowData(row, index) {

        if (!row) {
            return null;
        }

        const lineId = this.getRowLineId(row);

        const product = this.getRowProduct(row);

        return {
            key: lineId
                ? `line-${lineId}`
                : `row-${index}`,
            lineId: lineId,
            productName: product.name,
            pending: product.pending,
            quantity: this.getRowQuantity(row),
        };
    }


    buildCurrentSnapshot() {

        const snapshot = new Map();

        this.getOrderLineRows().forEach((row, index) => {

            const data = this.getManualRowData(row, index);

            if (!data) {
                return;
            }

            // Typing ke doran purani known state rakho
            if (data.pending) {

                const previous = this.manualSnapshot.get(data.key);

                if (previous) {

                    snapshot.set(data.key, previous);

                } else {

                    snapshot.set(
                        data.key,
                        { ...data, productName: "", pending: false }
                    );
                }

                return;
            }

            snapshot.set(data.key, data);
        });

        return snapshot;
    }


    updateManualSnapshot() {

        this.manualSnapshot = this.buildCurrentSnapshot();
    }


    // =====================================================
    // CHECK MANUAL CHANGES
    // =====================================================

    checkManualChanges() {

        if (this.isManualChecking) {
            return;
        }

        if (!this.isSupportedModel()) {

            this.manualContext = null;

            return;
        }

        this.isManualChecking = true;

        try {

            const now = Date.now();

            // -------- Naya document khula: silent baseline --------

            const context = this.getContextKey();

            if (context !== this.manualContext) {

                this.manualContext = context;

                this.baselineUntil = now + 1200;

                this.manualSnapshot = new Map();

                this.manualHighlightLineId = null;
            }

            // -------- Barcode ke baad ignore window --------

            if (now < this.ignoreManualUntil) {
                return;
            }

            if (this.needsResnapshot) {

                this.needsResnapshot = false;

                this.updateManualSnapshot();

                return;
            }

            if (now < this.baselineUntil) {

                this.updateManualSnapshot();

                return;
            }

            // -------- Compare --------

            const current = this.buildCurrentSnapshot();

            // Purani lines jo ab nahi hain (line id re-key hone par)
            const removed = Array.from(
                this.manualSnapshot.values()
            ).filter(
                (old) => !current.has(old.key)
            );

            let changed = null;

            for (const cur of current.values()) {

                // Abhi product select nahi hua
                if (!cur.productName) {
                    continue;
                }

                const previous = this.manualSnapshot.get(cur.key);

                if (previous) {

                    // Product ya quantity badli
                    // (naya product = previous.productName empty tha)
                    if (
                        previous.productName !== cur.productName ||
                        previous.quantity !== cur.quantity
                    ) {
                        changed = cur;
                        break;
                    }

                    continue;
                }

                // Unseen key: kya ye purani line ka re-key hai?
                const index = removed.findIndex(
                    (old) =>
                        old.productName === cur.productName &&
                        old.quantity === cur.quantity
                );

                if (index !== -1) {

                    // Odoo ne line ka datapoint id badal diya:
                    // highlight ko naye id ke saath chalne do
                    if (
                        removed[index].lineId &&
                        removed[index].lineId === this.manualHighlightLineId
                    ) {
                        this.manualHighlightLineId = cur.lineId;
                    }

                    removed.splice(index, 1);

                    continue;
                }

                // Sach mein nayi line
                changed = cur;
                break;
            }

            this.manualSnapshot = current;

            if (changed) {

                console.log("MANUAL CHANGE DETECTED:", changed);

                this.applyManualHighlight(changed);

            } else {

                // OWL re-render ne class hata di ho to dobara lagao
                this.paintManualRow(false);
            }

        } finally {

            this.isManualChecking = false;
        }
    }


    applyManualHighlight(changed) {

        // IMPORTANT: purana barcode observer band karo, warna wo har
        // DOM change par scanned row dobara highlight karke manual
        // highlight ko override kar deta hai.
        this.stopBarcodeObserver();

        this.scanSequence++;

        this.manualHighlightLineId = changed.lineId || null;

        this.paintManualRow(true);
    }


    paintManualRow(scroll) {

        if (!this.manualHighlightLineId) {
            return;
        }

        const row = this.getOrderLineRows().find(
            (item) =>
                this.getRowLineId(item) ===
                this.manualHighlightLineId
        );

        if (!row) {
            return;
        }

        if (!row.classList.contains("barcode-scanned-line")) {

            this.removeAllHighlights();

            this.highlightRow(row);
        }

        if (scroll) {

            try {

                row.scrollIntoView({
                    behavior: "smooth",
                    block: "center",
                });

            } catch (error) {

                console.log("Manual scroll error:", error);
            }
        }
    }


    // =====================================================
    // HIGHLIGHT HELPERS
    // =====================================================

    highlightRow(row) {

        if (!row) {
            return;
        }

        row.classList.add("barcode-scanned-line");

        row.style.setProperty(
            "background-color",
            "#fff3cd",
            "important"
        );

        row.querySelectorAll("td").forEach((td) => {

            td.classList.add("barcode-scanned-cell");

            td.style.setProperty(
                "background-color",
                "#fff3cd",
                "important"
            );
        });
    }


    removeAllHighlights() {

        document
            .querySelectorAll(".barcode-scanned-line")
            .forEach((oldRow) => {

                oldRow.classList.remove("barcode-scanned-line");

                oldRow.style.removeProperty("background-color");

                oldRow.querySelectorAll("td").forEach((td) => {

                    td.classList.remove("barcode-scanned-cell");

                    td.style.removeProperty("background-color");
                });
            });
    }


    showMessage(message) {

        alert(message);
    }
}


// =========================================================
// REGISTER SERVICE
// =========================================================

registry.category("services").add(
    "barcode_order_scanner",
    {

        start(env) {

            const scanner = new BarcodeOrderScanner(env);

            scanner.start();

            return scanner;
        },
    }
);