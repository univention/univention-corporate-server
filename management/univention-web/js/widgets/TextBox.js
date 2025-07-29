/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"put-selector/put",
	"dojo/on",
	"dojo/when",
	"dojo/query",
	"dijit/form/ValidationTextBox",
	"umc/widgets/Icon",
	"umc/widgets/TextBoxMaxLengthChecker",
	"umc/widgets/_FormWidgetMixin",
	"umc/tools"
], function(declare, lang, put, on, when, query, ValidationTextBox, Icon, TextBoxMaxLengthChecker, _FormWidgetMixin,
		tools) {
	return declare("umc.widgets.TextBox", [ ValidationTextBox, _FormWidgetMixin ], {
		// dynamicValue: String|Function
		//		Either a UMC command to query a value from or a javascript function.
		//		The javascript function may return a String or a dojo/Deferred object.
		dynamicValue: null,

		// depends: String?|String[]?
		//		Specifies that values need to be loaded dynamically depending on
		//		other form fields.
		depends: null,

		// umcpCommand:
		//		Reference to the umcpCommand the widget should use.
		//		In order to make the widget send information such as module flavor
		//		etc., it can be necessary to specify a module specific umcpCommand
		//		method.
		umcpCommand: lang.hitch(tools, 'umcpCommand'),

		// softMaxLength: {?Number}
		//		The maximum number of characters that should be adhered to.
		//		This maximum is not forced as it is with the 'maxLength' property
		//		(inherited from dijit/form/_TextBoxMixin.js).
		//		Instead, a tooltip with the 'softMaxLengthMessage' is displayed.
		softMaxLength: null,

		// softMaxLengthMessage: {String} [softMaxLengthMessage='']
		//		The message that is shown as tooltip when 'softMaxLength' is specified
		//		and overstepped.
		//		(softMaxLengthMessage can be an HTML string)
		softMaxLengthMessage: '',

		// we really do not want autofill as default.
		// autocomplete="off" is ignored by some browsers due to
		// https://www.w3.org/TR/html-design-principles/#priority-of-constituencies
		// and autofill being and desired feature for users.
		// As workaround we set autocomplete to a random string that does not resemble any
		// attribute like 'username' or 'street' that could prompt an autofill.
		// https://html.spec.whatwg.org/multipage/form-control-infrastructure.html#autofill
		autocomplete: '__JLM1J04IWVJD__',
		_setAutocompleteAttr: { node: 'focusNode', type: 'attribute' },

		// inlineLabel: String
		//		If specified, the given string is positioned as label above the input field.
		inlineLabel: null,
		_inlineLabelNode: null,

		_createInlineLabelNode: function(value) {
			this._inlineLabelNode = put(this.focusNode, '-span.umcInlineLabel', value);
			this.own(on(this._inlineLabelNode, 'click', lang.hitch(this, 'focus')));
		},

		_updateInlineLabelVisibility: function(eventType) {
			var showInlineLabel = !this.get('value') && eventType != 'keydown';
			put(this._inlineLabelNode, showInlineLabel ? '.umcEmptyValue' : '!umcEmptyValue');
		},

		_registerInlineLabelEvents: function() {
			this.on('keydown', lang.hitch(this, '_updateInlineLabelVisibility', 'keydown'));
			this.on('click', lang.hitch(this, '_updateInlineLabelVisibility', 'keydown'));
			this.on('focus', lang.hitch(this, '_updateInlineLabelVisibility', 'focus'));
			this.on('blur', lang.hitch(this, '_updateInlineLabelVisibility', 'blur'));
		},

		_setInlineLabelAttr: function(value) {
			if (!this._inlineLabelNode) {
				return;
			}

			// update node content
			put(this._inlineLabelNode, '', {
				innerHTML: value
			});

			// notify observers
			this._set('inlineLabel', value);
		},

		buildRendering: function() {
			this.inherited(arguments);

			// replace icon
			var icon = new Icon({
				'class': 'umcTextBox__validationIcon',
				iconName: 'alert-circle'
			});
			var validationContainerNode = query('.dijitValidationContainer', this.domNode)[0];
			put(validationContainerNode, '+', icon.domNode);
			put(validationContainerNode, '!');


			if (this.inlineLabel !== null) {
				this._createInlineLabelNode(this.inlineLabel);
				this._registerInlineLabelEvents();
				this._updateInlineLabelVisibility();
			}
			if (this.softMaxLength) {
				new TextBoxMaxLengthChecker({
					maxLength: this.softMaxLength,
					warningMessage: this.softMaxLengthMessage,
					textBoxWidget: this
				});
			}
		},

		//FIXME: the name should be different from _loadValues, e.g., _dependencyUpdate,
		//       and the check for all met dependencies should be done in the Form
		_loadValues: function(/*Object?*/ params) {
			// mixin additional options for the UMC command
			if (this.dynamicOptions && typeof this.dynamicOptions == "object") {
				lang.mixin(params, this.dynamicOptions);
			}

			// get the dynamic values, block concurrent events for value loading
			var func = tools.stringOrFunction(this.dynamicValue, this.umcpCommand);
			var deferredOrValues = func(params);

			// make sure we have an array or a dojo/Deferred object
			if (deferredOrValues) {
				when(deferredOrValues, lang.hitch(this, function(res) {
					this.set('value', res);
				}));
			}
		},

		_setValueAttr: function(newVal) {
			this.inherited(arguments);
			if (this._inlineLabelNode) {
				this._updateInlineLabelVisibility();
			}
		},

		// this seems to be necessary for IE8:
		// https://forge.univention.org/bugzilla/show_bug.cgi?id=28498
		_getValueAttr: function() {
			var val = this.inherited(arguments);
			if (val === '') {
				// seriously! at least it should not break anything...
				// although val === '', json.stringify returns ""null"" in IE8
				val = '';
			}
			return val;
		}
	});
});


