/*
 * Copyright 2011-2019 Univention GmbH
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
	"put-selector/put",
	"dojo/on",
	"dojo/when",
	"dijit/form/ValidationTextBox",
	"umc/widgets/TextBoxMaxLengthChecker",
	"umc/widgets/_FormWidgetMixin",
	"umc/tools"
], function(declare, lang, put, on, when, ValidationTextBox, TextBoxMaxLengthChecker, _FormWidgetMixin, tools) {
	return declare("umc.widgets.TextBox", [ ValidationTextBox, _FormWidgetMixin ], {
		// dynamicValue: String|Function
		//		Either an UMCP command to query a value from or a javascript function.
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
			// mixin additional options for the UMCP command
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


