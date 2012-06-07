/*
 * Copyright 2011-2012 Univention GmbH
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
dojo.require("umc.widgets.Form");

dojo.declare("umc.modules._setup.HelpPage", [ umc.widgets.Page, umc.i18n.Mixin ], {
	// summary:
	//		This class renderes a detail page containing subtabs and form elements
	//		in order to edit UDM objects.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.setup',

	// system-setup-boot
	wizard_mode: false,

	// __systemsetup__ user is logged in at local firefox session
	local_mode: false,

	postMixInProperties: function() {
		this.inherited(arguments);

		this.title = this._('Help');
		this.headerText = this._('UCS initial configuration');
		this._orgVals = {};
	},

	buildRendering: function() {
		this.inherited(arguments);

		// get the help file in the correct locale
		var path = dojo.locale.split(/[^a-zA-Z]/)[0].toLowerCase() + '/' + 'help.html';
		var html = dojo.cache('umc.modules._setup', path);

		// parse out the h1-header and set it as page title
		var regH1 = /<h1>([^<]*)<\/h1>/i;
		var match = html.match(regH1);
		if (match && match[1]) {
			this.set('headerText', match[1]);
			html = html.replace(regH1, '');
		}

		// build up the widgets
		// create the language combobox
		var widgets = [{
			type: 'LanguageBox',
			name: 'language',
			label: this._('Please choose the language of the wizard')
		}, {
			type: 'Text',
			name: 'html',
			label: '',
			content: html
		}];

		var form = new umc.widgets.Form({
			widgets: widgets,
			layout: ['language', 'html'],
			scrollable: true
		});

		var pane = new umc.widgets.ExpandingTitlePane({
			title: this._('Information about the initial configuration')
		});
		this.addChild(pane);

		pane.addChild(form);
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



