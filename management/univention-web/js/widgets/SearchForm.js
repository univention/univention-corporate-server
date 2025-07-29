/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/topic",
	"dojo/on",
	"umc/tools",
	"umc/widgets/Form",
	"umc/i18n!"
], function(declare, lang, array, domClass, topic, on, tools, Form, _) {
	return declare("umc.widgets.SearchForm", Form, {
		// summary:
		//		Encapsulates a complete search form with standard search and cancel
		//		buttons. This builds on top of umc/widgets/Form.

		// the widget's class name as CSS class
		baseClass: 'umcSearchForm',

		_parentModule: undefined,

		_publishPrefix: null,

		hideSubmitButton: false,

		doDisableSubmitWhileFormValuesLoad: false,

		_isSubmitButtonSpecified: function() {
			return array.some(this.buttons, function(ibutton) {
				return ibutton.name == 'submit';
			});
		},

		_isSubmitButtonSpecifiedInLayout: function() {
			var stack = [this.layout];
			while (stack.length) {
				var el = stack.pop();
				if (el instanceof Array) {
					array.forEach(el, function(i) {
						stack.push(i);
					});
				}
				else if ('submit' == el) {
					return true;
				}
			}
			return false;
		},

		postMixInProperties: function() {
			// in case no buttons are defined, define the standard 'submit' button
			if (!this._isSubmitButtonSpecified()) {
				if (!this.buttons) {
					this.buttons = [];
				}
				this.buttons.push({
					name: 'submit',
					showLabel: false,
					// label: _('Search'),
					'class': 'ucsIconButtonHighlighted',
					iconClass: 'search'
				});
			}

			// add the submit button next to the last widget in the layout
			if (!this._isSubmitButtonSpecifiedInLayout()) {
				var lastLayoutRow = this.layout.pop();
				if (typeof lastLayoutRow == 'string') {
					// row is specified by a string, i.e., containing a single element in a row
					lastLayoutRow = [lastLayoutRow, 'submit'];
				}
				else if (lastLayoutRow instanceof Array) {
					// last row is an array containing multiple elements
					lastLayoutRow.push('submit');
				}
				// put the last row back into the layout
				this.layout.push(lastLayoutRow);
			}

			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			var button = this._buttons.submit;
			if (button) {
				var labelPaneNode = lang.getObject('$refLabel$.domNode', false, button);
				var node = labelPaneNode || button.domNode;

				if (this.hideSubmitButton) {
					// hide the submit button
					domClass.add(node, 'dijitDisplayNone');
				} else if (!button.showLabel) {
					// add specific CSS classes for placing the default submit button
					// next to its preceding widget
					domClass.add(button.domNode, 'ucsButton--textfieldAligned');
					var previousWidget = node.previousSibling;
					if (previousWidget) {
						domClass.add(previousWidget, 'umcSearchFormElementBeforeSubmitButton');
					}
				}
			}
		},

		postCreate: function() {
			this.inherited(arguments);

			this.on('submit', lang.hitch(this, function() {
				this.onSearch(this.get('value'));

				// publish action event when search has been submitted
				if (this._parentModule === undefined) {
					this._parentModule = tools.getParentModule(this);
				}
				if (!this._parentModule) {
					// could not determine our parent module
					return;
				}

				// inverse the localized subtab title
				topic.publish('/umc/actions', this._parentModule.moduleID, this._parentModule.moduleFlavor, this._publishPrefix, 'search');
			}));

			if (this.doDisableSubmitWhileFormValuesLoad) {
				this._disabledSubmitUntilReady();
				on(this, 'updatingDependencies', lang.hitch(this, function() {
					this._disabledSubmitUntilReady();
				}));
			}
		},

		_disableSubmitUntilReadyDeferred: null,
		_disabledSubmitUntilReady: function() {
			this._buttons.submit.set('disabled', true);
			if (this._disabledSubmitUntilReadyDeferred && !this._disabledSubmitUntilReadyDeferred.isFulfilled()) {
				return;
			}
			this._disableSubmitUntilReadyDeferred = this.ready();
			this._disableSubmitUntilReadyDeferred.then(lang.hitch(this, function() {
				this._buttons.submit.set('disabled', false);
			}));
		},

		onSearch: function(values) {
			// event stub
		}
	});
});
