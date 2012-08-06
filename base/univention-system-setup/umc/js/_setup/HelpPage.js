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
dojo.require("umc.widgets._WidgetsInWidgetsMixin");

dojo.declare("umc.modules._setup.HelpPage", [ umc.widgets.Page, umc.i18n.Mixin, umc.widgets._WidgetsInWidgetsMixin ], {
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
		var pane = new umc.widgets.ExpandingTitlePane({
			title: this._('Information about the initial configuration')
		});
		this.addChild(pane);

		if (umc.i18n.availableLanguages.length > 1) {
			var langContainer = this.adopt(umc.widgets.ContainerWidget, {
				style: "float: right; display: inner-block;"
			});
			dojo.forEach(umc.i18n.availableLanguages, function(ilang) {
				// create one button per language
				langContainer.addChild(new umc.widgets.Button({
					iconClass: "country-" + ilang.id.substring(3).toLowerCase(), // country flags, i.e. "us", not "en"
					callback: function() {
						umc.i18n.setLanguage(ilang.id);
					}
				}));
			});

			dojo.place(langContainer.domNode, pane._titlePane.domNode, 'first');
		}
		this.text = new umc.widgets.Text({
			content: html,
			style: "overflow: auto;"
		});
		pane.addChild(this.text);
	},

	setHelp: function(pages) {
		var help_html_steps = [];
		dojo.forEach(pages, function(page) {
			if (page.helpText) {
				help_html_steps.push('<li>' + page.helpText + '</li>');
			}
		});
		var html = this.text.content;
		html = html.replace('<!-- HELP -->', help_html_steps.join('\n'));
		this.text._setContentAttr(html);
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



