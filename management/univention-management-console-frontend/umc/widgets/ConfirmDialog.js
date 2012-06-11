/*
 * Copyright 2011-2012 Univention GmbH
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
/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.ConfirmDialog");

dojo.require("dijit.Dialog");
dojo.require("dijit.layout.ContentPane");
dojo.require("dojox.widget.Dialog");
dojo.require("umc.widgets.ContainerWidget");

dojo.declare('umc.widgets.ConfirmDialog', dijit.Dialog, {
	// summary:
	//		Class that provides a customizable confirmation dialog.
	//		(For easier access see umc.dialog.confirm().)
	// description:
	//		The dialog expects a title, a message, and a list of choices the
	//		user can choose from. For each choice, a callback handler can be
	//		specified.
	// example:
	// 		This is a simple basic example that demonstrates all provided features.
	// |	var myDialog = new umc.widgets.ConfirmDialog({
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
	// |	// instead of using the 'callback' property, we can also use dojo.connect()
	// |	dojo.connect(myDialog, 'onConfirm', function(answer) {
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
	options: [],

	// the widget's class name as CSS class
	'class': 'umcConfirmDialog',

	// our own settings
	closable: false,

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
		if (dojo.isString(this.message)) {
			var widget = new umc.widgets.Text({
				'class': 'umcConfirmDialogText',
				content: message
			});
			this._container.addChild(widget, 0);
		}
		if (dojo.isObject(this.message) && 'declaredClass' in this.message) {
			// message is a widget
			dojo.addClass(this.message.domNode, 'umcConfirmDialogText');
			this._container.addChild(this.message, 0);
		}
	},

	buildRendering: function() {
		this.inherited(arguments);

		// put buttons into separate container
		var buttons = new umc.widgets.ContainerWidget({
			style: 'text-align: center;',
			'class': 'umcButtonRow'
		});
		var defaultButton = null;
		dojo.forEach(this.options, dojo.hitch(this, function(ichoice, idx) {
			var button = new umc.widgets.Button({
				label: ichoice.label,
				defaultButton: true === ichoice['default'],
				onClick: dojo.hitch(this, function(values) {
					// the response is either a custom response or the choice (button) index
					var response = ichoice.name || idx;

					// send 'onClick' event
					this.onConfirm(response);

					// call custom callback if specified
					if (ichoice.callback) {
						ichoice.callback(response);
					}
				})
			});
			buttons.addChild(button);

			// remember default button
			if (ichoice['default']) {
				defaultButton = button;
			}
		}));

		// make sure that the default button is focused
		defaultButton = defaultButton || buttons.getChildren()[0];
		if (defaultButton) {
			this.connect(this, 'onFocus', function() {
				defaultButton.focus();
			});
		}

		// put the layout together
		this._container = new umc.widgets.ContainerWidget({});
		this._container.addChild(buttons);
		this._container.startup();

		// attach layout to dialog
		this.set('content', this._container);
	},

	postCreate: function() {
		this.inherited(arguments);
	},

	close: function() {
		// summary:
		//		Hides the dialog and destroys it after the fade-out animation.
		this.hide().then(dojo.hitch(this, function() {
			this.destroyRecursive();
		}));
	},

	onConfirm: function(/*String*/ choice) {
		// summary:
		//		Event that is fired when the user confirms the dialog
		//		either with true or false.
		// choice:
		//		The key of option that has been chosen.
	},

	destroy: function() {
		this.inherited(arguments);
		this._container.destroyRecursive();
	}
});


