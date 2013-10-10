/*
 * Copyright 2013 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dijit/registry",
	"dijit/focus",
	"umc/tools",
	"umc/widgets/Wizard",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, registry, focusUtil, tools, Wizard, _) {

	return declare("umc.modules.udm.wizards.CreateWizard", [ Wizard ], {
		autoValidate: true,
		autoFocus: true,

		detailForm: null,
		detailButtons: null,

		widgetPages: null,

		_getPageWidgets: function(layout) {
			var widgets = [];
			array.forEach(layout, function(row) {
				widgets = widgets.concat(row);
			});
			return widgets;
		},

		buildWidget: function(widgetName, originalWidget, type) {
			return {
				name: widgetName,
				sizeClass: originalWidget.sizeClass,
				label: originalWidget.label,
				required: originalWidget.required,
				type: type,
				value: originalWidget.get('value')
			};
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			var pages = [];
			this._connectWidgets = [];
			array.forEach(this.widgetPages, lang.hitch(this, function(page) {
				var layout = page.widgets;
				var widgets = [];
				var pageName = 'page' + pages.length;
				var pageWidgets = this._getPageWidgets(layout);
				array.forEach(pageWidgets, lang.hitch(this, function(widgetName) {
					var originalWidget = this.detailForm.getWidget(widgetName);
					var type = originalWidget.declaredClass.substr(originalWidget.declaredClass.lastIndexOf('.') + 1);
					widgets.push(this.buildWidget(widgetName, originalWidget, type));
					this._connectWidgets.push({page: pageName, widget: widgetName});
				}));
				pages.push({
					name: pageName,
					headerText: page.title,
					helpText: page.helpText,
					widgets: widgets,
					layout: layout
				});
			}));
			lang.mixin(this, {
				pages: pages
			});
		},

		connectWidget: function(wizardWidget, wizardForm, detailWidget) {
			wizardForm.ready().then(lang.hitch(this, function() {
				this.own(wizardWidget.watch('value', function(attr, oldVal, newVal) {
					detailWidget.set('value', newVal);
				}));
			}));
		},

		buildRendering: function() {
			this.inherited(arguments);
			array.forEach(this._connectWidgets, lang.hitch(this, function(pageWidget) {
				var wizardWidget = this.getWidget(pageWidget.page, pageWidget.widget);
				var wizardForm = this._pages[pageWidget.page]._form;
				var detailWidget = this.detailForm.getWidget(pageWidget.widget);
				this.connectWidget(wizardWidget, wizardForm, detailWidget);
			}));
		},

		getFooterButtons: function() {
			var buttons = this.inherited(arguments);
			array.forEach(buttons, lang.hitch(this, function(button) {
				if (button.name === 'finish') {
					array.some(this.detailButtons, function(detailButton) {
						if (detailButton.name === 'submit') {
							button.label = detailButton.label;
							return true;
						}
					});
				}
				if (button.name === 'cancel') {
					array.some(this.detailButtons, function(detailButton) {
						if (detailButton.name === 'close') {
							button.label = detailButton.label;
							return true;
						}
					});
				}
			}));
			buttons.unshift({
				name: 'advance',
				label: _('Advanced'),
				align: 'right',
				callback: lang.hitch(this, 'onAdvanced')
			});
			return buttons;
		},

		onFinished: function() {
			var focusNode = focusUtil.curNode;
			if (focusNode) {
				var focusWidget = registry.byId(focusNode.id);
				if (focusWidget) {
					// force watch handler to fire _before_ on('Finished').
					//   otherwise the value from the wizard is not set to the underlying
					//   UDM form while validating
					focusWidget.set('value', focusWidget.get('value'));
				}
			}
		},

		onAdvanced: function() {
		}
	});
});

