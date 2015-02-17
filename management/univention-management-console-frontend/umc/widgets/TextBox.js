/*
 * Copyright 2011-2014 Univention GmbH
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
	"put-selector/put",
	"dojo/on",
	"dojo/when",
	"dijit/form/ValidationTextBox",
	"umc/widgets/_FormWidgetMixin",
	"umc/tools"
], function(declare, lang, put, on, when, ValidationTextBox, _FormWidgetMixin, tools) {
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

		// inlineLabel: String
		//		If specified, the given string ias positioned as label above the input field.
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


