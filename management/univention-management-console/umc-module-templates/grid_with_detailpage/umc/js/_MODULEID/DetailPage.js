/*
 * Copyright 2011 Univention GmbH
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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._MODULEID.DetailPage");

dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.modules._MODULEID.DetailPage", [ umc.widgets.Page, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	// summary:
	//		This class represents the detail view of our dummy module.

	// reference to the module's store object
	moduleStore: null,

	// use i18n information from umc.modules.MODULEID
	i18nClass: 'umc.modules.MODULEID',

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	postMixInProperties: function() {
		// is called after all inherited properties/methods have been mixed
		// into the object (originates from dijit._Widget)

		// it is important to call the parent's postMixInProperties() method
		this.inherited(arguments);

		// Set the opacity for the standby animation to 100% in order to mask
		// GUI changes when the module is opened. Call this.standby(true|false)
		// to enabled/disable the animation.
		this.standbyOpacity = 1;

		// set the page header
		this.headerText = this._('Object properties');
		this.helpText = this._('This page demonstrates how object properties can be viewed for editing.');

		// configure buttons for the footer of the detail page
		this.footerButtons = [{
			name: 'submit',
			label: this._('Save'),
			callback: dojo.hitch(this, function() {
				this._save(this._form.gatherFormValues());
			})
		}, {
			name: 'back',
			label: this._('Back to overview'),
			callback: dojo.hitch(this, 'onClose')
		}];
	},

	buildRendering: function() {
		// is called after all DOM nodes have been setup
		// (originates from dijit._Widget)

		// it is important to call the parent's postMixInProperties() method
		this.inherited(arguments);

		this.renderDetailPage();
	},

	renderDetailPage: function() {
		// render the form containing all detail information that may be edited

		// specify all widgets
		var widgets = [{
			type: 'TextBox',
			name: 'id',
			label: this._('Identifier'),
			disabled: true
		}, {
			type: 'TextBox',
			name: 'name',
			label: this._('Displayed name'),
			description: this._('Name that is displayed')
		}, {
			type: 'ComboBox',
			name: 'color',
			label: this._('Favorite color'),
			description: this._('Favorite color associated with the current entry'),
			dynamicValues: 'MODULEID/colors'
		}];

		// specify the layout... additional dicts are used to group form elements
		// together into title panes
		var layout = [{
			label: this._('Read-only properties'),
			layout: [ 'id' ]
		}, {
			label: this._('Editable properties'),
			layout: [ 'name', 'color' ]
		}];

		// create the form
		this._form = new umc.widgets.Form({
			widgets: widgets,
			layout: layout,
			moduleStore: this.moduleStore,
			// alows the form to be scrollable when the window size is not large enough
			scrollable: true
		});

		// add form to page... the page extends a BorderContainer, by default
		// an element gets added to the center region
		this.addChild(this._form);

		// hook to onSubmit event of the form
		this.connect(this._form, 'onSubmit', '_save');
	},

	_save: function(values) {
		umc.dialog.alert(this._('Feature not implemented yet!'));
	},

	load: function(id) {
		// during loading show the standby animation
		this.standby(true);

		// load the object into the form... the load method returns a
		// dojo.Deferred object in order to handel asynchronity
		this._form.load(id).then(dojo.hitch(this, function() {
			// done, switch of the standby animation
			this.standby(false);
		}), dojo.hitch(this, function() {
			// error handler: switch of the standby animation
			// error messages will be displayed automatically
			this.standby(false);
		}));
	},

	onClose: function(dn, objectType) {
		// event stub 
	}
});



