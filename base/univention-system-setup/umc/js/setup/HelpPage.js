/*
 * Copyright 2011-2013 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/dom-construct",
	"dojo/cache",
	"umc/widgets/Page",
	"umc/widgets/ExpandingTitlePane",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/i18n/tools",
	"umc/i18n!umc/modules/setup"
], function(declare, kernel, array, construct, cache, Page, ExpandingTitlePane, Text, ContainerWidget, Button, i18nTools, _) {

	return declare("umc.modules.setup.HelpPage", [ Page ], {
		// summary:
		//		This class renderes a detail page containing subtabs and form elements
		//		in order to edit UDM objects.

		// system-setup-boot
		wizard_mode: false,

		// __systemsetup__ user is logged in at local firefox session
		local_mode: false,

		postMixInProperties: function() {
			this.inherited(arguments);

			this.title = _('Help');
			this.headerText = _('UCS initial configuration');
			this._orgVals = {};
		},

		buildRendering: function() {
			this.inherited(arguments);

			// get the help file in the correct locale
			var path = kernel.locale.split(/[^a-zA-Z]/)[0].toLowerCase() + '/' + 'help.html';
			var html = cache('umc.modules.setup', path);

			// parse out the h1-header and set it as page title
			var regH1 = /<h1>([^<]*)<\/h1>/i;
			var match = html.match(regH1);
			if (match && match[1]) {
				this.set('headerText', match[1]);
				html = html.replace(regH1, '');
			}

			// build up the widgets
			var pane = new ExpandingTitlePane({
				title: _('Information about the initial configuration')
			});
			this.addChild(pane);

			if (i18nTools.availableLanguages.length > 1) {
				var langContainer = this.own(new ContainerWidget({
					style: "float: right; display: inner-block;"
				}))[0];
				array.forEach(i18nTools.availableLanguages, function(ilang) {
					// create one button per language
					langContainer.addChild(new Button({
						iconClass: "country-" + ilang.id.substring(3).toLowerCase(), // country flags, i.e. "us", not "en"
						'class': 'umcIconOnly',
						callback: function() {
							i18nTools.setLanguage(ilang.id);
						}
					}));
				});

				construct.place(langContainer.domNode, pane._titlePane.domNode, 'first');
			}
			this.text = new Text({
				content: html,
				style: "overflow: auto;"
			});
			pane.addChild(this.text);
		},

		setHelp: function(pages) {
			var help_html_steps = [];
			array.forEach(pages, function(page) {
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
});
