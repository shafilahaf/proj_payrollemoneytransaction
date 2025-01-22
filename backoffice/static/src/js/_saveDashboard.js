/** @odoo-module **/

import BoardView from 'board.BoardView';
import core from 'web.core';
import dataManager from 'web.data_manager';

var QWeb = core.qweb;

BoardView.prototype.config.Controller.include({
custom_events: _.extend({}, BoardView.prototype.config.Controller.prototype.custom_events, {
save_dashboard: '_saveDashboard',
}),

/**

Actually save a dashboard
@OverRide
@returns {Promise}
*/
_saveDashboard: function () {
var board = this.renderer.getBoard();
var arch = QWeb.render('DashBoard.xml', _.extend({}, board));
return this._rpc({
route: '/web/view/edit_custom',
params: {
custom_id: this.customViewID ? this.customViewID : "",
arch: arch,
}
}).then(dataManager.invalidate.bind(dataManager));
},
});