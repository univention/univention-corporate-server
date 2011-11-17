/*
 * Copyright 2011 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global console MyError dojo dojox dijit umc window */

dojo.provide("umc.modules.printers"); 

dojo.require("umc.i18n");
dojo.require("umc.dialog");
dojo.require("umc.widgets.ConfirmDialog");
dojo.require("umc.tools");

// ----------- sub pages ---------------
dojo.require("umc.modules._printers.OverviewPage");
dojo.require("umc.modules._printers.DetailPage");
dojo.require("umc.modules._printers.QuotaPage");

dojo.declare("umc.modules.printers", [
	umc.widgets.Module,
	umc.i18n.Mixin
	],
{

	i18nClass: 			'umc.modules.printers',
	
	_quota_from_page:	'',			// remembers the page from which the 'editQuota' was called
	
	buildRendering: function() {

		this.inherited(arguments);
		
		this._pages = {
			'overview':		new umc.modules._printers.OverviewPage(),
			'detail':		new umc.modules._printers.DetailPage(),
			'quota':		new umc.modules._printers.QuotaPage()
		};

		// forIn behaves like forEach just for dicts :) ... important it checks for hasOwnProperty!
		umc.tools.forIn(this._pages, function(iname, ipage) {
			this.addChild(ipage);
		}, this);

		// -------------- Events for page switching ----------------

		dojo.connect(this._pages['overview'],'openDetail',dojo.hitch(this,function(args) {
			this._switch_page('detail',args);
		}));
		
		dojo.connect(this._pages['overview'],'editQuota',dojo.hitch(this, function(args) {
			this._quota_from_page = 'overview';
			this._switch_page('quota',args);
		}));
		
		dojo.connect(this._pages['detail'],'editQuota',dojo.hitch(this, function(args) {
			this._quota_from_page = 'detail';
			this._switch_page('quota',args);
		}));
		
		dojo.connect(this._pages['detail'],'closeDetail',dojo.hitch(this, function(args) {
			this._switch_page('overview',args);
		}));
		
		dojo.connect(this._pages['quota'],'closeQuota',dojo.hitch(this, function(args) {
			this._switch_page(this._quota_from_page,args);
		}));
		
		// ------------- work events: printer management ---------------
		
		dojo.connect(this._pages['overview'],'managePrinter',dojo.hitch(this, function(printer,func,callback) {
			this._manage_printer(printer,func,callback);
		}));
		dojo.connect(this._pages['detail'],'managePrinter',dojo.hitch(this, function(printer,func,callback) {
			this._manage_printer(printer,func,callback);
		}));
 	},
 	
 	startup: function() {
 		
 		this.inherited(arguments);
 		
 		this._switch_page('overview');
 	},
 	
 	_switch_page: function(name, args) {
 		
 		if ((args) && (typeof (this._pages[name].setArgs) == 'function'))
		{
			this._pages[name].setArgs(args);
		}
 		
 		this.selectChild(this._pages[name]);
 		
 	},
 	
 	// Most management functions can be called from overview or detail view, so we write
 	// the functions here.
 	_manage_printer: function(printer,func,callback) {
 		
 		var cmd = '';
 		var args = {};
 		switch(func)
 		{
 			case 'activate':
 				cmd = 'printers/enable';
 				args = { printer: printer, on: true };
 				break;
 			case 'deactivate':
 				cmd = 'printers/enable';
 				args = { printer: printer, on: false };
 				break;
 		}
 		if (cmd)
 		{
 			umc.tools.umcpCommand(cmd,args).then(
 				dojo.hitch(this, function(data) {
 					if (data.result.length)
 					{
 						callback(false,data.result);
 					}
 					else
 					{
 						callback(true);
 					}
 				}),
 				dojo.hitch(this, function(data) {
 					callback(false,data.result);
 				})
 			);
 		}
 	}
	
});
