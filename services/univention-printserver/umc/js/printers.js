/*
 * Copyright 2011-2019 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/aspect",
	"umc/tools",
	"umc/widgets/Module",
	"umc/modules/printers/OverviewPage",
	"umc/modules/printers/DetailPage",
	"umc/modules/printers/QuotaPage",
	"umc/i18n!umc/modules/printers"
], function(declare, lang, aspect, tools, Module, OverviewPage, DetailPage, QuotaPage, _) {

	return declare("umc.modules.printers",  [ Module ], {

		_quota_from_page:	'',			// remembers the page from which the 'editQuota' was called

		buildRendering: function() {
			this.inherited(arguments);

			this._pages = {
				'overview':		new OverviewPage(),
				'detail':		new DetailPage(),
				'quota':		new QuotaPage()
			};

			// forIn behaves like forEach just for dicts :) ... important it checks for hasOwnProperty!
			tools.forIn(this._pages, function(iname, ipage) {
				this.addChild(ipage);
			}, this);

			// -------------- Events for page switching ----------------

			this.own(aspect.after(this._pages.overview,'openDetail',lang.hitch(this,function(args) {
				this._switch_page('detail',args);
			}),true));

			this.own(aspect.after(this._pages.overview,'editQuota',lang.hitch(this, function(args) {
				this._quota_from_page = 'overview';
				this._switch_page('quota',args);
			}),true));

			this.own(aspect.after(this._pages.detail,'editQuota',lang.hitch(this, function(args) {
				this._quota_from_page = 'detail';
				this._switch_page('quota',args);
			}),true));

			this.own(aspect.after(this._pages.detail,'closeDetail',lang.hitch(this, function(args) {
				this._switch_page('overview',args);
			}),true));

			this.own(aspect.after(this._pages.quota,'closeQuota',lang.hitch(this, function(args) {
				this._switch_page(this._quota_from_page,args);
			}),true));

			// ------------- work events: printer management ---------------

			this.own(aspect.after(this._pages.overview,'managePrinter',lang.hitch(this, function(printer,func,callback) {
				this._manage_printer(printer,func,callback);
			}),true));
			this.own(aspect.after(this._pages.detail,'managePrinter',lang.hitch(this, function(printer,func,callback) {
				this._manage_printer(printer,func,callback);
			}),true));
 		},

 		startup: function() {
 			this.inherited(arguments);

 			this._switch_page('overview');
 		},

 		_switch_page: function(name, args) {
 			if ((args) && (typeof (this._pages[name].setArgs) == 'function')) {
				this._pages[name].setArgs(args);
			}

 			this.selectChild(this._pages[name]);
 		},

 		// Most management functions can be called from overview or detail view, so we write
 		// the functions here.
 		_manage_printer: function(printer,func,callback) {

 			var cmd = '';
 			var args = {};
 			switch(func) {
 				case 'activate':
 					cmd = 'printers/enable';
 					args = { printer: printer, on: true };
 					break;
 				case 'deactivate':
 					cmd = 'printers/enable';
 					args = { printer: printer, on: false };
 					break;
 			}

 			if (cmd) {
 				tools.umcpCommand(cmd,args).then(lang.hitch(this, function(data) {
 					if (data.result.length) {
 						callback(false,data.result);
 					} else {
 						callback(true);
 					}
 				}), lang.hitch(this, function(data) {
 					callback(false,data.result);
 				}));
 			}
 		}

	});
});
