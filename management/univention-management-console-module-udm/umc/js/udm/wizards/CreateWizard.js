/*
 * Copyright 2013-2019 Univention GmbH
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
	"dojo/_base/array",
	"dojo/has",
	"umc/tools",
	"umc/widgets/Wizard",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, has, tools, Wizard, _) {

	return declare("umc.modules.udm.wizards.CreateWizard", [ Wizard ], {
		autoValidate: true,
		autoFocus: !has('touch'),

		detailPage: null,

		widgetPages: null,

		_getPageWidgets: function(layout) {
			var widgets = [];
			array.forEach(layout, function(row) {
				widgets = widgets.concat(row);
			});
			return widgets;
		},

		objectName: function() {
			var name = this.objectTypeName;
			var idx = name.indexOf(':');
			if (idx > -1) {
				// "Computers: Linux" -> "Linux"
				name = name.slice(idx + 2);
			}
			if (this._identifyingValue) {
				name = name + ' "' + this._identifyingValue + '"';
			}
			return name;
		},

		buildWidget: function(widgetName, originalWidgetDefinition) {
			if (originalWidgetDefinition.multivalue) {
				this._multiValuesWidgets.push(widgetName);
				originalWidgetDefinition = lang.clone(originalWidgetDefinition);
				originalWidgetDefinition.type = 'TextBox';
			}
			return lang.mixin(lang.clone(originalWidgetDefinition), {
				name: widgetName,
				sizeClass: originalWidgetDefinition.size,
				label: originalWidgetDefinition.label,
				required: originalWidgetDefinition.required,
				type: originalWidgetDefinition.type
			});
		},

		getValues: function() {
			var values = this.inherited(arguments);
			tools.forIn(lang.clone(values), lang.hitch(this, function(key, value) {
				if (array.indexOf(this._multiValuesWidgets, key) !== -1) {
					values[key] = [value];
				}
			}));
			return values;
		},

		setCustomValues: function(values, detailPageForm) {
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this._mayFinishDeferred = this.detailPage.ready();
			this._detailButtons = this.detailPage.getButtonDefinitions();
			this._multiValuesWidgets = [];
			this._identifyingAttribute = null;
			var pages = [];
			array.forEach(this.widgetPages, lang.hitch(this, function(page) {
				var layout = page.widgets;
				var widgets = [];
				var pageName = 'page' + pages.length;
				var pageWidgets = this._getPageWidgets(layout);
				array.forEach(pageWidgets, lang.hitch(this, function(widgetName) {
					var originalWidgetDefinition = array.filter(this.properties, function(prop) { return prop.id == widgetName; })[0];
					if (originalWidgetDefinition && originalWidgetDefinition.identifies) {
						this._identifyingAttribute = widgetName;
					}
					widgets.push(this.buildWidget(widgetName, originalWidgetDefinition));
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

		buildRendering: function() {
			var _labelText = lang.hitch(this, function() {
				var text = {
					'users/user'        : _('Loading user...'),
					'groups/group'      : _('Loading group...'),
					'computers/computer': _('Loading computer...'),
					'networks/network'  : _('Loading network object...'),
					'dns/dns'           : _('Loading DNS object...'),
					'dhcp/dhcp'         : _('Loading DHCP object...'),
					'shares/share'      : _('Loading share...'),
					'shares/print'      : _('Loading printer...'),
					'mail/mail'         : _('Loading mail object...'),
					'nagios/nagios'     : _('Loading Nagios object...'),
					'policies/policy'   : _('Loading policy...')
				}[this.detailPage.moduleFlavor];
				if (!text) {
					text = _('Loading LDAP object...');
				}
				return text;
			});

			this.inherited(arguments);
			var allWidgets = {};
			tools.forIn(this._pages, lang.hitch(this, function(pageName, page) {
				var finishButton = page._footerButtons.finish;
				var originalLabel = finishButton.get('label');
				finishButton.set('disabled', true);
				finishButton.set('label', _labelText());
				this._mayFinishDeferred.then(function() {
					finishButton.set('label', originalLabel);
					finishButton.set('disabled', false);
				});
				lang.mixin(allWidgets, page._form._widgets);
			}));

			this.templateObject = this.detailPage.buildTemplate(this.template, this.properties, allWidgets);
		},

		getFooterButtons: function(pageName) {
			var buttons = this.inherited(arguments);
			array.forEach(buttons, lang.hitch(this, function(button) {
				if (button.name === 'finish') {
					array.some(this._detailButtons, function(detailButton) {
						if (detailButton.name === 'submit') {
							button.label = detailButton.label;
							return true;
						}
					});
				}
			}));
			if (pageName == 'page0' && this.preWizardAvailable) {
				buttons.unshift({
					name: 'back_to_pre_wizard',
					label: _('Back'),
					align: 'right',
					callback: lang.hitch(this, function() {
						this.onBackToFirstPage();
					})
				});
			}
			buttons.unshift({
				name: 'advance',
				label: _('Advanced'),
				align: 'right',
				callback: lang.hitch(this, function() {
					this.onAdvanced(this.getValues());
				})
			});
			return buttons;
		},

		_finish: function() {
			var values = this.getValues();
			this._identifyingValue = values[this._identifyingAttribute];
			return this.inherited(arguments);
		},

		canFinish: function() {
			return this.inherited(arguments) && this._mayFinishDeferred.isResolved();
		},

		onBackToFirstPage: function() {
		},

		onAdvanced: function() {
		}
	});
});

