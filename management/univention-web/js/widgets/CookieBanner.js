/*
 * Copyright 2011-2020 Univention GmbH
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
	"dijit/Dialog",
	"dijit/TitlePane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/widgets/Text"
], function(declare, lang, array, query, domClass, Dialog, TitlePane, ContainerWidget, Button, Text) {
	// in order to break circular dependencies
	// we define dijit/registry as empty object and
	// require it explicitly
	var registry = {
		byNode: function() {}
	};
	require(["dijit/registry"], function(_registry) {
		registry = _registry;
	});

	return declare("umc.widgets.CookieBanner", [ Dialog ], {
		// summary:
		//		Class that provides a customizable cookie banner dialog.
		//		(For easier access see dialog.cookieBanner().)
		// description:
		//		The cookie banner expects a title, the main message and a handler 
		//		which is called when clicking the confirmation button.
		// example:
		// 		This is a simple basic example that demonstrates all provided features.
		// |	var myBanner = new CookieBanner({
		// |		title: 'Cookie-Settings',
		// |		message: 'We are using Cookies on our website. Click on the accept button to use this portal',
		// |		confirmCallback:  function() {
		// |			// do something after cookie confirmation
		// |			// e.g. set default cookies
		// |		}
		// |	});

		// title: String
		//		The title of the cookie banner window.
		title: 'Cookie-Banner',

		// message: String
		//		The cookie text message to be displayed
		message: 'We are using Cookies on our website. Click the button to use this portal',

		// confirmCallback: Function
		//		A user specified function without parameters that is called when the cookie
		//		accept button was clicked and the cookie banner closes.
		confirmCallback: function() {
			console.log("cookies confirmed")
		},

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
			var widget = new Text({
				content: message + " [set]",
				'class': 'umcConfirmDialogText'
			});
			this._container.addChild(widget, 0);
			
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this.baseClass += ' umcCookieBanner';
		},

		buildRendering: function() {
			this.inherited(arguments);

			// put the accept button into separate container
			var buttons = new ContainerWidget({
				'class': 'umcButtonRow'
			});
			var acceptButton = new Button({
				defaultButton: true,
				label: "Accept",
				onClick: lang.hitch(this, function() {
					// send 'confirm' event
					this.onConfirm();
				})
			});

			buttons.addChild(acceptButton);

			// make sure that the accept button is focused
			this.own(this.on('focus', function() {
				acceptButton.focus();
			}));

			// put the layout together
			this._container = new ContainerWidget({});
			this._container.addChild(buttons);
			this._container.startup();

			// explicitly set 'closable' here, otherwise it does not have any effect
			// this.set('closable', this.closable);

			// attach layout to dialog
			this.set('content', this._container);
		},

		close: function() {
			// summary:
			//		Hides the dialog and destroys it after the fade-out animation.
			this.hide().then(lang.hitch(this, function() {
				this.destroyRecursive();
			}));
		},

		onConfirm: function(/*String*/ choice) {
			// summary:
			//		Event that is fired when the user confirms the cookie banner
			this.confirmCallback()
		},

		destroy: function() {
			this.inherited(arguments);
			this._container.destroyRecursive();
		}
	});
});

