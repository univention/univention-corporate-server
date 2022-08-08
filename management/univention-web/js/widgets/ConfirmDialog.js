/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2011-2022 Univention GmbH
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
/*global define,require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/query",
	"dojo/dom-class",
	"dijit/TitlePane",
	"dijit/_WidgetsInTemplateMixin",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/widgets/Dialog",
	"umc/widgets/Text",
	"put-selector/put"
], function(declare, lang, array, query, domClass, TitlePane, _WidgetsInTemplateMixin, ContainerWidget, Button, Dialog, Text, put) {
	// in order to break circular dependencies
	// we define dijit/registry as empty object and
	// require it explicitly
	var registry = {
		byNode: function() {}
	};
	require(["dijit/registry"], function(_registry) {
		registry = _registry;
	});

	return declare("umc.widgets.ConfirmDialog", [ Dialog, _WidgetsInTemplateMixin ], {
		// summary:
		//		Class that provides a customizable confirmation dialog.
		//		(For easier access see dialog.confirm().)
		// description:
		//		The dialog expects a title, a message, and a list of choices the
		//		user can choose from. For each choice, a callback handler can be
		//		specified.
		// example:
		// 		This is a simple basic example that demonstrates all provided features.
		// |	var myDialog = new ConfirmDialog({
		// |		title: 'Please confirm...',
		// |		message: 'Please confirm <b>now</b>!',
		// |		options: [{
		// |		    label: 'Do nothing',
		// |			name: 'nothing'
		// |		}, {
		// |		    label: 'Do something',
		// |			name: 'something',
		// |			callback: function() {
		// |				// we may provide a callback handler directly
		// |				// ... we need to close the dialog manually
		// |				myDialog.close();
		// |			}
		// |		}]
		// |	});
		// |
		// |	// instead of using the 'callback' property, we can also use on()
		// |	on(myDialog, 'confirm', function(answer) {
		// |		if ('something' == answer) {
		// |			// do something
		// |			// ...
		// | 			// dialog will be closed by the callback function
		// |		}
		// |		else {
		// |			// close the dialog for the choice 'nothing'
		// |			myDialog.close();
		// |		}
		// |	});

		// message: String|Object
		//		The message to be displayed, can also be a widget.
		message: '',

		// title: String
		//		The title of the dialog window.
		title: '',

		// options: Object[]
		//		Array of objects with all available choices (=buttons). Each entry must have the
		//		property 'label' and may have a 'callback', i.e., a user specified function
		//		that is called. The optional property 'default' renders the corresponding
		//		button in the style of a submit button. The callback will receive as parameter
		//		the option chosen, i.e., an integer or - if specified - the corresponding
		//		'name' property of the button.
		options: null,

		actionBarTemplate: '<div data-dojo-type="umc/widgets/ContainerWidget" data-dojo-attach-point="actionBar" class="umcDialogActionBar dijitDisplayNone"></div>',

		_container: null,

		_setMessageAttr: function(message) {
			this.message = message;
			var childs = this._container.getChildren();
			if (childs.length > 1) {
				// a message/widget has been added previously... remove it
				this._container.removeChild(childs[0]);
				childs[0].destroyRecursive();
			}

			// add the new message
			if (typeof this.message == "string") {
				var widget = new Text({
					content: message,
				});
				this._container.addChild(widget, 0);
			}
			if (typeof this.message == "object" && 'declaredClass' in this.message) {
				// message is a widget
				var widgets = [this.message]; // fallback: check self
				if (this.containerNode) {
					widgets = query("[widgetId]", this.message.containerNode).map(registry.byNode);
				}
				array.forEach(widgets, lang.hitch(this, function(widget) {
					if (widget.isInstanceOf(TitlePane)) {
						this.own(widget._wipeIn.on('End', lang.hitch(this, function() {
							this._relativePosition = null;
							this._size();
							this._position();
						})));
						this.own(widget._wipeOut.on('End', lang.hitch(this, function() {
							this._relativePosition = null;
							this._size();
							this._position();
						})));
					}
				}));
				this._container.addChild(this.message, 0);
			}
		},

		constructor: function() {
			this.options = [];
		},

		_setOptionsAttr: function(options) {
			this.actionBar.destroyDescendants();
			array.forEach(options, lang.hitch(this, function(ichoice, idx) {
				var props = lang.mixin({}, ichoice, {
					'class': 'ucsTextButton',
					defaultButton: !!ichoice['default'],
					onClick: lang.hitch(this, function() {
						// the response is either a custom response or the choice (button) index
						var response = ichoice.name || idx;

						// send 'confirm' event
						this.onConfirm(response);

						// call custom callback if specified
						if (ichoice.callback) {
							ichoice.callback(response);
						}
					})
				});
				delete props.callback;
				delete props['default'];

				this.actionBar.addChild(new Button(props));
			}));
			domClass.toggle(this.actionBar.domNode, 'dijitDisplayNone', !options.length);
			this._set('options', options);
		},

		// if the _firstFocusItem is on the 'options' buttons then
		// we want to focus the default button if it exists
		_buttonToFocus: function() {
			var buttons = this.actionBar.getChildren();
			var firstButton = buttons[0];
			this._getFocusItems();
			if (firstButton && this._firstFocusItem === firstButton.focusNode) {
				var defaultButton = array.filter(buttons, function(button) {
					return button.defaultButton;
				})[0];
				if (defaultButton) {
					return defaultButton;
				}
			}
			return null;
		},

		focus: function() {
			var buttonToFocus = this._buttonToFocus();
			if (buttonToFocus) {
				buttonToFocus.focus();
			} else {
				this.inherited(arguments);
			}
		},

		show: function() {
			var promise = this.inherited(arguments);
			var buttonToFocus = this._buttonToFocus();
			if (buttonToFocus) {
				promise.then(function() {
					buttonToFocus.focus();
				});
			}
			return promise;
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._container = new ContainerWidget({});
			this.addChild(this._container);
		},

		onConfirm: function(/*String*/ choice) {
			// summary:
			//		Event that is fired when the user confirms the dialog
			//		either with true or false.
			// choice:
			//		The key of option that has been chosen.
		}
	});
});

