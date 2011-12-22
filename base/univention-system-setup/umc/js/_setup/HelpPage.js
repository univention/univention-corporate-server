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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._setup.HelpPage");

dojo.require("dojo.cache");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.Text");

dojo.declare("umc.modules._setup.HelpPage", [ umc.widgets.Page, umc.i18n.Mixin ], {
	// summary:
	//		This class renderes a detail page containing subtabs and form elements
	//		in order to edit UDM objects.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.setup',

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('Help');
		this.headerText = this._('UCS appliance');
		this._orgVals = {};
	},

	buildRendering: function() {
		this.inherited(arguments);

		// get the help file in the correct locale
		var path = dojo.locale.split('-')[0].toLowerCase() + '/' + 'help.html';
		var html = dojo.cache('umc.modules._setup', path);

		// build up the widgets
		var pane = new umc.widgets.ExpandingTitlePane({
			title: this._('Information about UCS appliance mode')
		});
		this.addChild(pane);
		var text = new umc.widgets.Text({
			content: html,
			style: "overflow: auto;"
		});
		pane.addChild(text);
	},

	setValues: function(_vals) {
		// nothing to do
	},

	getValues: function() {
		// return empty dict
		return {};
	},

	getSummary: function() {
		// return empty array
		return [];
	},

	onSave: function() {
		// event stub
	}
});



