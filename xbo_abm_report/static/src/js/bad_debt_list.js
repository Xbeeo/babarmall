import {registry} from "@web/core/registry";
import {listView} from "@web/views/list/list_view";
import {ListController} from "@web/views/list/list_controller";
import {useService} from "@web/core/utils/hooks";

export class BadDebtListController extends ListController {
    setup() {
        super.setup();
        this.actionService = useService("action");
    }

    onClickBadDebtReport() {
        this.actionService.doAction("xbo_abm_report.action_bad_debt_report_wizard");
    }
}

registry.category("views").add("bad_debt_list", {
    ...listView,
    Controller: BadDebtListController,
    buttonTemplate: "BadDebtListButtons",
});