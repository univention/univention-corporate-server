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
	"dojo/Deferred",
	"dojo/dom-class",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Button",
	"umc/widgets/CheckBox",
	"umc/modules/udm/DetailPage",
	"umc/i18n!umc/modules/udm",
	"dijit/registry",
	"umc/widgets"
], function(declare, lang, array, Deferred, domClass, tools, dialog, Button, CheckBox, DetailPage, _ ) {
	return declare("umc.modules.udm.QuickDetailPage", [ DetailPage ], {
		buildRendering: function() {
			this.inherited(arguments);
			this._customFieldsKey = 'customWidgets/' + this.moduleFlavor;
		},

		_flattenFields: function(layout) {
			var fields = [];
			array.forEach(layout, lang.hitch(this, function(props) {
				if (props.layout) {
					fields = fields.concat(this._flattenFields(props.layout));
				} else if (typeof props == "string") {
					fields.push(props);
				} else if (props instanceof Array) {
					fields = fields.concat(props);
				}
			}));
			return fields;
		},

		renderDetailPage: function(_properties, _layout, policies, template, expressLayout) {
			var deferred = new Deferred();
			var properties = array.filter(_properties, function(prop) {
				return prop.id !== '$options$';
			});
			var originalArguments = arguments;
			var customFields;
			var hiddenFields;
			var customFieldsTitlePane;
			var hiddenFieldsTitlePane;
			properties.push({
				type: Button,
				id: '$addCustomsFieldsButton$',
				name: '$addCustomsFieldsButton$',
				label: _('Add/remove fields'),
				callback: lang.hitch(this, function() {
					var flattenedCustomFields = this._flattenFields(customFields);
					var fieldnames = flattenedCustomFields.concat(this._flattenFields(hiddenFields));
					fieldnames = array.filter(fieldnames, function(field) {
						return field !== '$addCustomsFieldsButton$';
					});
					var widgets = array.map(fieldnames, lang.hitch(this, function(field) {
						return {
							type: CheckBox,
							name: field,
							label: this._form.getWidget(field).label,
							value: flattenedCustomFields.indexOf(field) !== -1
						};
					}));
					var options = {
						title: _('Add/remove fields'),
						widgets: widgets,
						submit: _('Add/remove fields')
					};
					dialog.confirmForm(options).then(lang.hitch(this, function(values) {
						customFields = [];
						hiddenFields = [];
						tools.forIn(values, lang.hitch(this, function(widgetName, custom) {
							var widget = this._form.getWidget(widgetName);
							if (custom) {
								customFields.push(widgetName);
								customFieldsTitlePane.content.addChild(widget.$refLabel$.getParent());
							} else {
								hiddenFields.push(widgetName);
								hiddenFieldsTitlePane.content.addChild(widget.$refLabel$.getParent());
							}
						}));
						var preferences = {};
						preferences[this._customFieldsKey] = customFields.join(',');
						tools.setUserPreference(preferences);
						customFieldsTitlePane.content.addChild(this._form.getWidget('$addCustomsFieldsButton$').$refLabel$.getParent());
					}));
				})
			});
			var layout = _layout;
			if (expressLayout && expressLayout.length) {
				var expressFields = this._flattenFields(expressLayout);
				customFields = [];
				tools.getUserPreferences().then(lang.hitch(this, function(preferences) {
					var customFieldsPreferences = preferences[this._customFieldsKey];
					if (customFieldsPreferences) {
						customFields = customFieldsPreferences.split(',');
					} else {
						customFields = [];
					}
					customFields.push('$addCustomsFieldsButton$');
					hiddenFields = this._flattenFields(_layout);
					var requiredFields = array.filter(hiddenFields, function(field) {
						return field.required;
					});
					var layoutFields = expressFields.concat(requiredFields).concat(customFields);
					hiddenFields = array.filter(hiddenFields, function(field) {
						return layoutFields.indexOf(field) === -1;
					});
					layout = [{
						advanced: false,
						layout: expressLayout,
						label: _('Add (simplified)')
					}];
					if (requiredFields.length) {
						layout[0].layout.push({
							label: _('Required fields'),
							layout: requiredFields
						});
					}
					layout[0].layout.push({
						label: _('Other fields'),
						layout: customFields
					});
					layout[0].layout.push({
						label: _('Hidden fields'),
						layout: hiddenFields
					});
					originalArguments[0] = properties;
					originalArguments[1] = layout;
					originalArguments[2] = [];
					var renderDetailPageDeferred = this.inherited(originalArguments);
					renderDetailPageDeferred.then(lang.hitch(this, function() {
						customFieldsTitlePane = layout[0].layout[layout[0].layout.length-2].$refTitlePane$;
						hiddenFieldsTitlePane = layout[0].layout[layout[0].layout.length-1].$refTitlePane$;
						domClass.add(hiddenFieldsTitlePane.id, 'dijitHidden');
					}));
					renderDetailPageDeferred.then(lang.hitch(deferred, 'resolve'), lang.hitch(deferred, 'reject'));
				}));
			} else {
				deferred = this.inherited(originalArguments);
			}
			return deferred;
		}
	});

});

