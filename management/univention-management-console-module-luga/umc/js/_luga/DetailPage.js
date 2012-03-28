/*
 * Copyright 2012 Univention GmbH
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

dojo.provide("umc.modules._luga.DetailPage");

dojo.require("umc.dialog");
dojo.require("umc.i18n");
dojo.require("umc.tools");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.modules._luga.PasswordInputBox");

dojo.declare("umc.modules._luga.DetailPage", [ umc.widgets.Page, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	// summary:
	//		This class represents the detail view of our dummy module.

	// reference to the module's store object
	moduleStore: null,

	// use i18n information from umc.modules.luga
	i18nClass: 'umc.modules.luga',

	// internal reference to the formular containing all form widgets of an UDM object
	_form: null,

	// new object?
	newObject: null,

	// initial object properties as they are represented by the form
	_receivedObjFormData: null,

	postMixInProperties: function() {
		// is called after all inherited properties/methods have been mixed
		// into the object (originates from dijit._Widget)

		// it is important to call the parent's postMixInProperties() method
		this.inherited(arguments);

		// Set the opacity for the standby animation to 100% in order to mask
		// GUI changes when the module is opened. Call this.standby(true|false)
		// to enable/disable the animation.
		this.standbyOpacity = 1;

		// set the page header
		if (this.moduleFlavor === 'luga/users') {
			this.headerText = this._('Properties for user %s', '');
			this.helpText = this._('Create or modify an local user.');
		} else if (this.moduleFlavor === 'luga/groups') {
			this.headerText = this._('Group properties');
			this.helpText = this._('Create or modify a group with the form displayed below.');
		}

		// configure buttons for the footer of the detail page
		this.footerButtons = [{
			name: 'submit',
			label: this._('Save'),
			callback: dojo.hitch(this, '_save')
		}, {
			name: 'back',
			label: this._('Back to overview'),
			callback: dojo.hitch(this, 'confirmClose')
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
		var widgets;
		var layout;
		if (this.moduleFlavor === 'luga/users') {
			// specify all widgets
			widgets = [{
				type: 'TextBox',
				name: 'username',
				label: this._('Username')
			}, {
				type: 'umc.modules._luga.PasswordInputBox',
				name: 'password',
				label: this._('Password')
			}, {
				type: 'NumberSpinner',
				name: 'uid',
				size: 'OneThird',
				label: this._('User ID')
			}, {
			// Groups
				type: 'ComboBox',
				name: 'group',
				label: this._('Primary group'),
				dynamicValues: 'luga/groups/get_groups'
			}, {
				type: 'MultiSelect',
				name: 'groups',
				label: this._('Additional Groups'),
				dynamicValues: 'luga/groups/get_groups'
			}, {
			// Unix/Posix
				type: 'TextBox',
				name: 'homedir',
//				size: 'TwoThirds',
				label: this._('Unix home directory')
			}, {
				type: 'TextBox',
				name: 'shell',
				label: this._('Login shell')
			}, {
			// Gecos
				type: 'TextBox',
				name: 'fullname',
				label: this._('Full name')
			}, {
				type: 'TextBox',
				name: 'roomnumber',
				label: this._('Room number')
			}, {
				type: 'TextBox',
				name: 'tel_business',
				label: this._('Telephone (business)')
			}, {
				type: 'TextBox',
				name: 'tel_private',
				label: this._('Telephone (private)')
			}, {
				type: 'TextBox',
				name: 'miscellaneous',
				label: this._('Miscellaneous')
			}, {
			// Status information
				type: 'CheckBox',
				name: 'lock',
				label: this._('Disable login')
			}, {
				type: 'CheckBox',
				name: 'pw_is_expired',
				disabled: true,
				label: this._('Password is expired')
			}, {
				type: 'CheckBox',
				name: 'pw_delete',
				value: false,
				label: this._('Remove password')
			}, {
				type: 'CheckBox',
				name: 'pw_is_empty',
				disabled: true,
				label: this._('The password is currently not set')
			}, {
				type: 'DateBox',
				disabled: true,
				name: 'pw_last_change',
				label: this._('Password was last changed')
			}, {
				type: 'TextBox',
				name: 'pw_mindays',
				type: 'NumberSpinner',
				label: this._('Days before password may be changed')
			}, {
				type: 'TextBox',
				name: 'pw_maxdays',
				type: 'NumberSpinner',
				label: this._('Days after which password must be changed')
			}, {
				type: 'TextBox',
				name: 'pw_warndays',
				type: 'NumberSpinner',
				label: this._('Days before password expiration that user is warned')
			}, {
				type: 'TextBox',
				name: 'pw_disabledays',
				type: 'NumberSpinner',
				label: this._('Days after password expiration where account will be disabled')
			}, {
				// This field will be hidden if account is enabled
				type: 'DateBox',
				disabled: true,
				name: 'disabled_since',
				label: this._('Account is disabled since')
			}, {
				type: 'CheckBox',
				name: 'create_home',
				label: this._('move home folder')
			}];

			// specify the layout... additional dicts are used to group form elements
			// together into title panes
			layout = [{
				label: this._('General'),
				layout: [ [ 'username', 'fullname' ], ['password'], ['lock', 'pw_delete' ] ]
			}, { 
				label: this._('Additional information'),
				layout: [ ['tel_business', 'tel_private'], ['roomnumber', 'miscellaneous'] ]
			}, {
				label: this._('Groups'),
				layout: [ 'group', 'groups' ]
			}, {
				label: this._('Account information'),
				layout: [ 'uid', 'shell',  'homedir', 'create_home']
			}, {
				label: this._('Options and Passwords'),
				layout: [ 'pw_is_expired', 'pw_is_empty', ['pw_last_change', 'disabled_since'], ['pw_mindays', 'pw_maxdays'], ['pw_warndays', 'pw_disabledays'] ]
			}];
		} else if (this.moduleFlavor === 'luga/groups') {
			widgets = [{
				type: 'TextBox',
				name: 'groupname',
				label: this._('Groupname')
			}, {
				type: 'TextBox',
				name: 'gid',
				label: this._('Group ID')
			}, {
				type: 'MultiSelect',
				name: 'users',
				label: this._('Users'),
				dynamicValues: 'luga/users/get_users'
			}, {
				type: 'MultiSelect',
				name: 'administrators',
				label: this._('Administrators'),
				dynamicValues: 'luga/users/get_users'
			}];
			layout = [];
		}

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

	getAlteredValues: function() {
		// summary:
		//		Return a list of object properties that have been altered.

		// get all form values and see which values are new
		var vals = this._form.gatherFormValues();
		var newVals = {};
		if (this.newObject) {
			// get only non-empty values
			umc.tools.forIn(vals, dojo.hitch(this, function(iname, ival) {
				if (!(dojo.isArray(ival) && !ival.length) && ival) {
					newVals[iname] = ival;
				}
			}));
		}
		else {
			// existing object .. get only the values that changed
			umc.tools.forIn(vals, function(iname, ival) {
				var oldVal = this._receivedObjFormData[iname];

				// check whether old values and new values differ...
				if (!umc.tools.isEqual(ival,oldVal)) {
					newVals[iname] = ival;
				}
			}, this);

			// set the original username
			if (this.moduleFlavor === 'luga/users') {
				newVals.$username$ = this._receivedObjFormData.username;
			}
			else if (this.moduleFlavor === 'luga/groups') {
				newVals.id = this._receivedObjFormData.groupname;
			}
		}
		return newVals;
	},

	_save: function() {
		// summary:
		//		Save the user changes for the edited object.

		// TODO: validate form entries

		var values = this.getAlteredValues();

		var deferred = null;
		if (this.newObject) {
			deferred = this.moduleStore.add(values);
		}
		else {
			deferred = this.moduleStore.put(values);
		}
		deferred.then(dojo.hitch(this, function(result) {
			// see whether saving was successfull
			this.standby(false);

			if (result.length === 0) {
				// everything ok, close page
				this.onClose();
			}
			else {
				// print error message to user
				umc.dialog.alert(escape(result));
			}
		}), dojo.hitch(this, function() {
			this.standby(false);
		}));
	},

	initConnects: function() {
		if (this.moduleFlavor === 'luga/users') {

			// Set group to username groupname is equal to original value / is not touched
			this.connect(this._form.getWidget('username'), 'onChange', dojo.hitch(this, function(username) {
				var equal = this._receivedObjFormData.group === this._form.getWidget('group').get('value');

				if (!this._newObject || equal) {
					this._form.getWidget('group').set('staticValues', [username]);
					this._form.setValues({
						homedir: '/home/'+username,
						group: username
					});
				} else {
					this.disconnect();
				}
			}));

			// modifiing Objects
			if (!this._newObject) {
				// deactivate create_home (move hom folder) button if values has not changed and not new object
				this.connect(this._form.getWidget('homedir'), 'onChange', dojo.hitch(this, function(homedir) {
					var equal = (this._receivedObjFormData.homedir === homedir);
					this._form.getWidget('create_home').set('disabled', equal);
					if (!equal) {
						this.disconnect();
					}
				}));

			}

			// disable/enable password field to value of lock and pw_remove
			dojo.forEach(['lock', 'pw_delete'], function(widget) {
				this.connect(this._form.getWidget(widget), 'onChange', dojo.hitch(this, function(locked) {
					var lock = this._form.getWidget('lock').get('value');
					var remove = this._newObject ? false : this._form.getWidget('pw_delete').get('value');
					if (!locked) {
						locked = !lock && !remove;
					}
					this._form.getWidget('password').setDisabledAttr(locked);
					//this._form.getWidget('password').set('disabled', locked); // FIXME
				}));
			}, this);

		}
	},

	_resetForm: function() {
		this._form.clearFormValues();
		umc.tools.forIn(this._form._widgets, function(widget) {
			var w = this._form.getWidget(widget);
			w.set('visible', true);
			if(w.reset) {
				w.reset();
			}
		}, this);
		// TODO: set all values unchecked
//		this._form.getWidget('group').set('value', []);
	},

	add: function() {
		// add a local user or group
		this.newObject = true;
		this._resetForm();
		if (this.moduleFlavor === 'luga/users') {
			umc.tools.forIn({ 
				pw_is_expired: ['visible', false],
				pw_is_empty: ['visible', false],
				pw_last_change: ['visible', false],
				disabled_since: ['visible', false],
				pw_delete: ['visible', false],
				uid: ['visible', false],
				create_home: ['label', this._('Create home folder')],
				create_home: ['checked', true],
				shell: ['value', '/bin/bash'],
				pw_maxdays: ['value', 99999],
				pw_mindays:  ['value', 0],
				pw_warndays:  ['value', 7],
				pw_disabledays:  ['value', '']
			}, function(widget, value) {
				this._form.getWidget(widget).set(value[0], value[1]);
			}, this);
		} else if (this.moduleFlavor === 'luga/groups') {
			this._form._widgets.gid.set('visible', false);
		}

		this.initConnects();

		this.standby(false);
	},

	load: function(id) {
		// during loading show the standby animation
		this.standby(true);

		this.newObject = false;

		this._resetForm();

		// load the object into the form... the load method returns a
		// dojo.Deferred object in order to handel asynchronity
		this._form.load(id).then(dojo.hitch(this, function() {
			// done, switch of the standby animation
			this._receivedObjFormData = this._form.gatherFormValues();
			this.standby(false);
		}), dojo.hitch(this, function() {
			// error handler: switch of the standby animation
			// error messages will be displayed automatically
			this.standby(false);
		}));

		this.initConnects();
	},

	confirmClose: function() {
		this.onClose();
	},

	onClose: function() {
		// event stub 
	}
});




