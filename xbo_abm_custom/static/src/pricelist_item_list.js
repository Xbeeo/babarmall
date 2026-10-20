/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";

patch(X2ManyField.prototype, {
    get rendererProps() {
        const props = super.rendererProps;
        if (
            this.props.viewMode === "list" &&
            this.props.record.resModel === "product.pricelist" &&
            this.props.name === "item_ids"
        ) {
            const originalOnAdd = props.onAdd;
            // Add a line -> popup (editable: false makes onAdd call _openRecord)
            props.onAdd = (params = {}) => this.onAdd({ ...params, editable: false });
        }
        return props;
    },
});