/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"dojo/query",
	"dijit/form/FilteringSelect",
	"umc/widgets/_SelectMixin",
	"umc/widgets/_FormWidgetMixin",
	// StandbyMixin is used by _SelectMixin
	"umc/widgets/StandbyMixin",
	"umc/widgets/Icon",
	"./Button",
	"put-selector/put"
], function(declare, lang, on, query, FilteringSelect, _SelectMixin, _FormWidgetMixin, StandbyMixin, Icon, Button, put) {
	return declare("umc.widgets.ComboBox", [ FilteringSelect , _SelectMixin, _FormWidgetMixin, StandbyMixin ], {
		// search for the substring when typing
		queryExpr: '*${0}*',

		// no auto completion, otherwise this gets weird in combination with the '*${0}*' search
		autoComplete: false,

		// autoHide: Boolean
		//		If true, the ComboBox will only be visible if it lists more than
		//		one element.
		autoHide: false,

		_firstClick: true,

		postMixInProperties: function() {
			this.inherited(arguments);

			if (this.autoHide) {
				// autoHide is set, by default the widget will be hidden
				this.visible = false;
			}
		},

		_updateVisibility: function() {
			if (this.autoHide) {
				// show the widget in case there are more than 1 values
				var values = this.getAllItems();
				this.set('visible', values.length > 1);
			}
		},

		buildRendering: function() {
			this.inherited(arguments);

			// exchange validation icon node
			var iconNode = Icon.createNode('alert-circle', 'umcTextBox__validationIcon');
			var validationContainerNode = query('.dijitValidationContainer', this.domNode)[0];
			put(validationContainerNode, '+', iconNode);
			put(validationContainerNode, '!');

			// exchange dropdown icon node
			var buttonNode = Button.simpleIconButtonNode('chevron-down', 'ucsIconButton umcTextBox__downArrowButton');
			put(this._buttonNode, '+', buttonNode);
			put(this._buttonNode, '!');
			this._buttonNode = buttonNode;
		},

		postCreate: function() {
			this.inherited(arguments);
			this.on('valuesLoaded', lang.hitch(this, '_updateVisibility'));
		}
	});
});

