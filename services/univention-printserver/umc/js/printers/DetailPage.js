/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2011-2022 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojox/html/entities",
	"umc/tools",
	"umc/store",
	"umc/widgets/Page",
	"umc/widgets/Grid",
	"umc/widgets/Form",
	"umc/widgets/Text",
	"umc/i18n!umc/modules/printers"
], function(declare, lang, domClass, entities, tools, store, Page, Grid, Form, Text, _) {
	return declare("umc.modules.printers.DetailPage", [ Page ], {
		navContentClass: 'umcCard2',

		_printer_id: '',

		postMixInProperties: function() {
			lang.mixin(this,{
				helpText: _("You see the details of this printer and its print jobs. You can activate/deactivate the printer and cancel print jobs."),
				headerText: _("Printer details")
			});

			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			var f_widgets = [{
				name: 'message',
				type: Text,
				content: '<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;',
				style: 'padding-bottom:.5em;' // force bottom distance to the buttons
			}];

			var f_layout = [
				[ 'message' ],
				[ 'activate', 'deactivate' ]
			];

			var f_buttons = [{
				name: 'activate',
				label: _("Activate"),
				title: _("Activate this printer"),
				onClick: lang.hitch(this, function() {
					tools.umcpCommand('printers/enable', { printer: this._printer_id, on: true }).then(lang.hitch(this, function() {
						this._refresh_view();
					}));
				})
			}, {
				name: 'deactivate',
				label: _("Deactivate"),
				title: _("Deactivate this printer"),
				onClick: lang.hitch(this, function() {
					tools.umcpCommand('printers/enable', { printer: this._printer_id, on: false }).then(lang.hitch(this, function() {
						this._refresh_view();
					}));
				})
			}];

			// we make this a form so we can add buttons
			this._head = new Form({
				region: 'nav',
				widgets: f_widgets,
				buttons: f_buttons,
				layout: f_layout,
				onSubmit: function() {} // don't want to have any kind of submit here!
			});
			this.addChild(this._head);

			var columns = [{
				name: 'job',
				label: _("Job")
			}, {
				name: 'owner',
				label: _("Owner")
			}, {
				name: 'size',
				label: _("Size")
			}, {
				name: 'date',
				label: _("Submitted at")
			}];

			var actions = [{
				name: 'cancel',
				label: _("Cancel"),
				title: _("Cancel this job/these jobs"),
				isMultiAction: true,
				isStandardAction: true,
				callback: lang.hitch(this, function(ids) {
					tools.umcpCommand('printers/jobs/cancel',{jobs: ids, printer: this._printer_id}).always(lang.hitch(this, function() {
						this._refresh_view();
					}));
				})
			}, {
				name: 'back',
				label: _("Back to overview"),
				isContextAction: false,
				callback: lang.hitch(this, function() {
					this.closeDetail();
				})
			}, {
				name: 'refresh',
				label: _("Refresh job list"),
				isContextAction: false,
				callback: lang.hitch(this, function() {
					this._refresh_view();
				})
			}];

			this._grid = new Grid({
				region: 'main',
				columns: columns,
				actions: actions,
				moduleStore: store('job','printers/jobs')
			});
			this.addChild(this._grid);
		},

		// Overview page passes args here. Arg is here the printer ID.
		setArgs: function(args) {
			this._printer_id = args;
			this._refresh_view();
		},

		// no matter where we came from: if the page is to be shown we
		// have to refresh all data elements.
		onShow: function() {
			this._refresh_view();
		},

		// called when the page is shown, but can equally be called
		// on a manual or automatic refresh.
		_refresh_view: function() {

			// if the function is called before setArgs has given us a valid printer name
			// then we should simply do nothing.
			if (!this._printer_id) {
				return;
			}

			tools.umcpCommand('printers/get',{printer:this._printer_id}).then(lang.hitch(this, function(data) {
				// Yes I know, I should have this done by the layout capabilities of
				// the Form class... but given the fact that this is only an informative
				// overview message I've decided to wrap it into a single 'Text' element,
				// containing a <p>..</p> and a <table>.
				var res = data.result;
				// styles
				var st_r = 'padding-left: var(--layout-spacing-unit);';  // right column

				// status text must be translated in our official wording...
				var status = _("unknown");
				switch(res['status']) {
					case 'enabled': status = _("active"); break;
					case 'disabled':status = _("inactive"); break;
				}

				var txt = "";
				txt += "<table style='font-size: var(--font-size-4);'>\n";
				txt += "<tr><td>" + _("Server")       + ":</td><td style='" + st_r + "'>" + entities.encode(res['server'])      + "</td></tr>\n";
				txt += "<tr><td>" + _("Status")       + ":</td><td style='" + st_r + "'>" + entities.encode(status)             + "</td></tr>\n";
				txt += "<tr><td>" + _("Location")     + ":</td><td style='" + st_r + "'>" + entities.encode(res['location'])    + "</td></tr>\n";
				txt += "<tr><td>" + _("Description")  + ":</td><td style='" + st_r + "'>" + entities.encode(res['description']) + "</td></tr>\n";
				txt += "</table>\n";

				this._head.getWidget('message').set('content',txt);

				// show/hide corresponding buttons

				this._show_button('activate',res['status'] == 'disabled');
				this._show_button('deactivate',res['status'] == 'enabled');
				this.onPrinterLoaded(res.printer);
			}), lang.hitch(this, function(data) {
				this._grid.filter(); // clears stale grid data
			}));

			// read job list
			this._grid.filter({printer: this._printer_id});
		},

		_show_button: function(button, on) {
			try {
				domClass.toggle(this._head._buttons[button].domNode, 'dijitDisplayNone', !on);
			} catch(ex) {
				console.error("show_button(" + button + "," + on + "): " + ex.message);
			}
		},

		// main module listens here to return to the overview.
		// args are passed back to the Overview page.
		closeDetail: function(args) {
			// force clean state
			this._head.getWidget('message').set('content','<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;<br/>&nbsp;'); // six empty lines
			this._grid.filter();
		},

		onPrinterLoaded: function(printer) {
			// stub
		}
	});
});
