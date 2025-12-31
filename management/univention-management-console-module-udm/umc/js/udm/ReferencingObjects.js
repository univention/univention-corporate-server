/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/topic",
	"umc/widgets/Button",
	"umc/widgets/Text",
	"umc/tools",
	"umc/app",
	"umc/widgets/ContainerWidget",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, topic, Button, Text, tools, app, ContainerWidget, _) {
	return declare("umc.modules.udm.ReferencingObjects", [ ContainerWidget ], {
		// summary:
		//		Provides a list of buttons opening a given object

		name: '',

		value: null,

		disabled: false,

		// the widget's class name as CSS class
		baseClass: 'umcReferencingObjects',

		_setValueAttr: function(value) {
			if (value instanceof Object) {
				this._set('value', value);
				this.destroyDescendants();
				if (Array.isArray(value)) {
					if (value.length) {
						array.forEach(value, lang.hitch(this, function(item) {
							this._addReferencingObjectLink(item);
						}));
					} else {
						this.addChild(new Text({
							content: _('No referencing objects')
						}));
					}
				}
			} else {
				console.log('ReferencingObjects: not an object');
			}
		},

		_addReferencingObjectLink: function(item) {

			//  make sure that the item has all necessary properties
			if (!array.every(['module', 'id', 'objectType'], function(ikey) {
				if (!(ikey in item)) {
					console.log('ReferencingObjects: attribute module is missing');
					return false;
				}
				return true;
			})) {
				// item has not all necessary properties -> stop here
				return false;
			}

			// perpare information to open the referenced UDM object
			var moduleProps = {
				flavor: item.flavor,
				module: item.module,
				openObject: {
					objectDN: item.id,
					objectType: item.objectType
				}
			};

			// create new button
			var btn = new Button({
				name: 'close',
				label: item.label,
				// iconClass: tools.getIconClass(item.icon, 20, null, "background-size: contain"),
				callback: function() {
					// open referenced UDM object
					if (app.getModule(moduleProps.module, moduleProps.flavor)) {
						topic.publish("/umc/modules/open", moduleProps.module, moduleProps.flavor, moduleProps);
					} else if (app.getModule(moduleProps.module, 'navigation')) {  // udm module
						topic.publish("/umc/modules/open", moduleProps.module, 'navigation', moduleProps);
					} else {
						topic.publish("/umc/modules/open", moduleProps.module, moduleProps.flavor, moduleProps);
					}
				}
			});

			this.addChild(btn);
		},

		isValid: function() {
			return true;
		}
	});
});
