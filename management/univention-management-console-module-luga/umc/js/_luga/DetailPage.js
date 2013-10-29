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

define([
	"umc.dialog",
	"umc.i18n",
	"umc.tools",
	"umc.widgets.Form",
	"umc.widgets.Page",
	"umc.widgets.StandbyMixin",
	"umc.modules._luga.PasswordInputBox"
], function(dialog, i18n, tools, Form, Page, StandbyMixin, PasswordInputBox) {

//	dojo.declare("umc.modules._luga.DetailPage", [ umc.widgets.Page, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	return {

		// reference to the module's store object
		moduleStore: null,

		// use i18n information from umc.modules.luga
		i18nClass: 'umc.modules.luga',

		// internal reference to the formular containing all form widgets of an UDM object
		_form: null,

		// new object?
		_newObject: null,

		// initial object properties as they are represented by the form, it is a cache if newObject
		_receivedObjFormData: null,

		objectNamePlural: null,
		objectNameSingular: null,

		postMixInProperties: function() {
			this.inherited(arguments);

			// Set the opacity for the standby animation to 100% in order to mask
			// GUI changes when the module is opened. Call this.standby(true|false)
			// to enable/disable the animation.
			this.standbyOpacity = 1;

			// set the page header
			if (this.moduleFlavor === 'users') {
				this.headerText = this._('Properties for user %s', '');
				this.helpText = this._('Create or modify an local user.');
			} else if (this.moduleFlavor === 'groups') {
				this.headerText = this._('Group properties');
				this.helpText = this._('Create or modify a local group');
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
			this.inherited(arguments);

			this.renderDetailPage();
		},

		renderDetailPage: function() {
			// render the form containing all detail information that may be edited
			var widgets, layout;

			var nameDescription = this._('May consist of up to 32 characters including letters, "ä, Ä, ü, Ü, ö, Ö", "_", "-", and not start with "-"');

			var validator = function(value) {
				return -1 === value.search(':');
			};

			var gecosValidator = function(value) {
				return validator(value) && (-1 === value.search(','));
			};

			if (this.moduleFlavor === 'users') {
				// specify all widgets
				widgets = [{
					type: 'TextBox',
					name: 'username',
					description: nameDescription,
					required: true,
					validator: function(value) {
						return null !== value.match(/^[a-zA-Z_][a-zA-Z0-9_\-]*[$]?$/);
					},
					label: this._('Username')
				}, {
					type: 'umc.modules._luga.PasswordInputBox',
					required: true,
					name: 'password',
					label: this._('Password')
				}, {
					type: 'NumberSpinner',
					name: 'uid',
					constraints: { min: 0, max: 400000000 },
					disabled: true,
					size: 'OneThird',
					label: this._('User ID')
				}, {
				// Groups
					type: 'ComboBox',
					name: 'group',
					validator: validator,
					label: this._('Primary group'),
					dynamicValues: 'luga/groups/get_groups'
				}, {
					type: 'MultiObjectSelect',
					name: 'groups',
					validator: validator,
					label: this._('Additional Groups'),
					formatter: function(ids) {
						dojo.forEach(ids, function(id, i) {
							if (dojo.isString(id)) { ids[i] = {label: id, id: id}; }
						});
						return ids;
					},
					queryWidgets: [ {
						type: 'ComboBox',
						name: 'category',
						label: this._('Category'),
						staticValues: [
							{id: 'groupname', label: this._('Groupname')},
							{id: 'gid', label: this._('Group ID')},
							{id: 'users', label: this._('Users')},
							{id: 'administrators', label: this._('Administrators')}
						]
					}, {
						type: 'TextBox',
						name: 'pattern',
						value: '*',
						label: this._('Search pattern')
					}, {
						type: 'ComboBox'
					}],
					queryCommand: dojo.hitch(this, function(options) { 
						return this.moduleStore.umcpCommand('luga/groups/get_groups', options).then(function(data) {
							return data.result;
						});
					}),
					autoSearch: true
				}, {
				// Unix/Posix
					type: 'TextBox',
					name: 'homedir',
					validator: validator,
					label: this._('Unix home directory')
				}, {
					type: 'TextBox',
					name: 'shell',
					validator: validator,
					label: this._('Login shell')
				}, {
				// Gecos
					type: 'TextBox',
					name: 'fullname',
					validator: gecosValidator,
					label: this._('Fullname')
				}, {
					type: 'TextBox',
					name: 'roomnumber',
					validator: gecosValidator,
					label: this._('Room number')
				}, {
					type: 'TextBox',
					name: 'tel_business',
					validator: gecosValidator,
					label: this._('Telephone (business)')
				}, {
					type: 'TextBox',
					name: 'tel_private',
					validator: gecosValidator,
					label: this._('Telephone (private)')
				}, {
					type: 'TextBox',
					name: 'miscellaneous',
					validator: gecosValidator,
					label: this._('Miscellaneous')
				}, {
				// Status information
					type: 'CheckBox',
					name: 'lock',
					label: this._('Disable login')
				}, {
					type: 'CheckBox',
					name: 'pw_remove',
					value: false,
					label: this._('Remove password')
				}, {
					type: 'DateBox',
					disabled: true,
					name: 'pw_last_change',
					label: this._('Password was last changed')
				}, {
					name: 'pw_mindays',
					type: 'NumberSpinner',
					constraints: { min: -1, max: 400000000 },
					label: this._('Days until the password may be changed')
				}, {
					name: 'pw_maxdays',
					type: 'NumberSpinner',
					constraints: { min: -1, max: 400000000 },
					label: this._('Days until the password has to be changed')
				}, {
					name: 'pw_warndays',
					type: 'NumberSpinner',
					constraints: { min: -1, max: 400000000 },
					label: this._('Days between password expiration and user notification')
				}, {
					name: 'pw_disabledays',
					type: 'NumberSpinner',
					constraints: { min: -1, max: 400000000 },
					label: this._('Days until the account will be disabled after password expiration')
				}, {
					// This field will be hidden if account is enabled
					type: 'DateBox',
					disabled: true,
					name: 'disabled_since',
					label: this._('Account is disabled since')
				}, {
					type: 'CheckBox',
					name: 'create_home',
					label: this._('Move home folder')
				}];

				// specify the layout... additional dicts are used to group form elements
				// together into title panes
				layout = [{
					label: this._('General'),
					layout: [ [ 'username', 'fullname' ], ['password'], ['lock', 'pw_remove' ] ]
				}, { 
					label: this._('Additional information'),
					layout: [ ['tel_business', 'tel_private'], ['roomnumber', 'miscellaneous'] ]
				}, {
					label: this._('Groups'),
					layout: [ 'group', 'groups' ]
				}, {
					label: this._('Account information'),
					layout: [ 'uid', 'shell',  'homedir']
				}, {
					label: this._('Options and Password'), // TODO: better description
					layout: [ 'pw_last_change', 'disabled_since', 'pw_mindays', 'pw_maxdays', 'pw_warndays', 'pw_disabledays' ]
				}];
			} else if (this.moduleFlavor === 'groups') {
				widgets = [{
					type: 'TextBox',
					name: 'groupname',
					label: this._('Groupname'),
					description: nameDescription,
					validator: function(value) {
						return validator(value) && ('-' !== value[0]);
					}
				}, {
					type: 'NumberSpinner',
					name: 'gid',
					label: this._('Group ID')
				}, {
					type: 'MultiObjectSelect',
					name: 'users',
					validator: validator,
					label: this._('Users'),
					formatter: function(ids) {
						dojo.forEach(ids, function(id, i) {
							if (dojo.isString(id)) { ids[i] = {label: id, id: id};}
						});
						return ids;
					},
					queryWidgets: [ {
						type: 'ComboBox',
						name: 'category',
						label: this._('Category'),
						staticValues: [
							{id: 'username', label: this._('Username')},
							{id: 'uid', label: this._('User ID')},
							{id: 'group', label: this._('Primary group')}
						]
					}, {
						type: 'TextBox',
						name: 'pattern',
						value: '*',
						label: this._('Search pattern')
					}, {
						type: 'ComboBox'
					}],
					queryCommand: dojo.hitch(this, function(options) { 
						return this.moduleStore.umcpCommand('luga/users/get_users', options).then(function(data) {
							return data.result;
						});
					}),
					autoSearch: true
				}];

				layout = [{
					label: this._('General'),
					layout: [ ['groupname', 'gid'] ]
				}, {
					label: this._('Group members'),
					layout: [ ['users'] ]
				}];
			}

			// create the form
			this._form = new Form({
				widgets: widgets,
				layout: layout,
				moduleStore: this.moduleStore,
				scrollable: true
			});

			// add form to page...
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

			// remove unneedet values
			delete vals.pw_last_change;
			delete vals.disabled_since;
			delete vals.uid;

			if (this._newObject) {
				// get only non-empty values
				tools.forIn(vals, dojo.hitch(this, function(iname, ival) {
					if (!(dojo.isArray(ival) && !ival.length) && ival) {
						newVals[iname] = ival;
					}
				}));
			}
			else {
				// existing object .. get only the values that changed
				tools.forIn(vals, function(iname, ival) {
					var oldVal = this._receivedObjFormData[iname];

					// the backend needs all fields of the "gecos"
					if (-1 !== dojo.indexOf(['fullname', 'tel_business', 'tel_private', 'miscellaneous', 'roomnumber' ], iname)) {
						newVals[iname] = ival;
						return true;
					}

					// check whether old values and new values differ...
					if (!tools.isEqual(ival,oldVal)) {
						newVals[iname] = ival;
					}
				}, this);
			}
			return newVals;
		},

		validateChanges: function(vals) {
			// summary:
			//		Validate the user input.

			// reset settings from last validation
			tools.forIn(this._form._widgets, function(iname, iwidget) {
				if (iwidget.setValid) {
					iwidget.setValid(null);
				}
			}, this);

			// check whether all required properties are set
			var errMessage = this._('The following properties need to be specified or are invalid:') + '<ul>';
			var allValuesGiven = true;
			tools.forIn(this._form._widgets, function(iname, iwidget) {
				// ignore widgets that are not visible
				if (!iwidget.get('visible') || !iwidget.get('disabled')) {
					return true;
				}

				// check whether a required property is set or a property is invalid
				var tmpVal = dojo.toJson(iwidget.get('value'));
				var isEmpty = tmpVal == '""' || tmpVal == '[]' || tmpVal == '{}';
				if ((isEmpty && iwidget.required) || (!isEmpty && iwidget.isValid && false === iwidget.isValid())) {
					// value is empty
					allValuesGiven = false;
					errMessage += '<li>' + iwidget.label + '</li>';
				}
			}, this);
			errMessage += '</ul>';

			// check whether any changes are made at all
			var nChanges = 0;
			var regKey = /\$.*\$/;
			tools.forIn(vals, function(ikey) {
				if (!regKey.test(ikey)) {
					// key does not start and end with '$' and is thus a regular key
					++nChanges;
				}
			});

			if (!nChanges) {
				dialog.alert(this._('No changes have been made.'));
				return false;
			}

			// print out an error message if not all required properties are given
			if (!allValuesGiven) {
				dialog.alert(errMessage);
				return false;
			}

			return true;
		},

		_save: function() {
			// summary:
			//		Save the user changes for the edited object.

			var values = this.getAlteredValues();

			if(!this.validateChanges(values)) {
				return;
			}

			if (this.moduleFlavor === 'users') {
				// set the original username
				values.$username$ = this._receivedObjFormData.username;

				// ask for moving homefolder
				if (!this._newObject && undefined !== values.homedir) {
					dialog.confirm(this._form.getWidget('create_home'), [{
						label: this._('OK'),
						callback: dojo.hitch(this, function() {
							values.create_home = this._form.getWidget('create_home').getValue();
							this._saveValues(values);
						})
					}, {
						label: this._('Cancel'),
						"default": true
					}]);
				} else {
					this._saveValues(values);
				}
			}
			else if (this.moduleFlavor === 'groups') {
				values.id = this._receivedObjFormData.groupname;
				this._saveValues(values);
			}
		},

		_saveValues: function(values) {
			var deferred = null;
			if (this._newObject) {
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
					var message = '';
					dojo.forEach(result, function(err) {
						if (!err.success) {
							message += err.message;
						}
					});
					if (message !== '') {
						dialog.alert(message);
					} else {
						this.onClose();
					}
				}
			}), dojo.hitch(this, function() {
				this.standby(false);
			}));
		},


		prepareFormGroups: function() {
			if (this._newObject) {
				this._form._widgets.gid.set('visible', false);
			}
		},

		prepareFormUsers: function() {
		//	summary:
		//		set some form values, add some connects
			// on adding a user
			if (this._newObject) {
				tools.forIn({ 
					pw_last_change: ['visible', false],
					disabled_since: ['visible', false],
					pw_remove: ['visible', false],
					uid: ['visible', false],
					create_home: ['checked', true],
					shell: ['value', '/bin/bash'],
					pw_maxdays: ['value', 99999],
					pw_mindays:  ['value', 0],
					pw_warndays:  ['value', 7],
					pw_disabledays:  ['value', '']
				}, function(widget, value) {
					this._form.getWidget(widget).set(value[0], value[1]);
				}, this);

				// Set group to username if group is not touched, same for homedir
				var c = this.connect(this._form.getWidget('username'), 'onChange', dojo.hitch(this, function(username) {
					var group, home;
					var groupequal = this._receivedObjFormData.group === (group = this._form.getWidget('group').get('value'));
					var homeequal = this._receivedObjFormData.homedir === (home = this._form.getWidget('homedir').get('value'));

					if (groupequal) {
						this._receivedObjFormData.group = username;
						this._form.getWidget('group').set('staticValues', [username]);
						this._form.getWidget('group').set('value', username);
					}
					if (homeequal) {
						this._receivedObjFormData.homedir = '/home/'+username;
						this._form.getWidget('homedir').set('value', '/home/'+username);
					}

					if (!homeequal && !groupequal) {
						this.disconnect(c);
					}
				}));
			}
			// on modifiing user
			else {
				// deactivate create_home (move home folder) button if values has not changed, don't disconnect
				this.connect(this._form.getWidget('homedir'), 'onChange', dojo.hitch(this, function(homedir) {
					this._form.getWidget('create_home').set('disabled', (this._receivedObjFormData.homedir === homedir));
				}));
				// disable/enable password field to value of pw_remove
				this.connect(this._form.getWidget('pw_remove'), 'onChange', dojo.hitch(this, function(enabled) {
					enabled = enabled || this._form.getWidget('lock').get('value');
					this._form.getWidget('password').setDisabledAttr(enabled);
				}));

				// hide disabled_since field if account is not disabled
				this._form.getWidget('disabled_since').set('visible', !this._form.getWidget('lock').get('value'));

				// disable userid field
				this._form.getWidget('uid').set('disabled', true);
			}

			// on adding and modifiing user

			// disable/enable password field to value of lock or (pw_remove if not new User)
			this.connect(this._form.getWidget('lock'), 'onChange', dojo.hitch(this, function(enabled) {
				if(!this._newObject) {
					enabled = enabled || this._form.getWidget('pw_remove').get('value');
				}
				this._form.getWidget('password').setDisabledAttr(enabled);
			}));
		},

		_resetForm: function() {
		// summary:
		//		clear and reset the form
			this._form.clearFormValues();
			tools.forIn(this._form._widgets, function(widget) {
				var w = this._form.getWidget(widget);
				if (undefined !== w.visible && !w.visible) {
					w.set('visible', true);
				}
				if(w.reset) {
					w.reset();
				}
				if (w.checked) {
					// CheckBox
					w.set('checked', false);
				}
				if (w.disabled) {
					w.set('disabled', false);
				}
			}, this);
			if (this.moduleFlavor === 'users') {
				this._form.getWidget('groups').set('value', []);
				if (this._newObject) {
					this._form.getWidget('group').set('value', '');
				}
			}
		},

		load: function(id) {
		// summary:
		//		open the detailpage for adding or modifiing a user or group
			this._newObject = (id === undefined);
			this._resetForm();

			this.standby(true);

			var deferred;
			if (this._newObject) {
				deferred = new dojo.Deferred();
				deferred.resolve();
			} else {
				// load the object into the form...
				deferred = this._form.load(id);
			}

			deferred.then(dojo.hitch(this, function() {
				this._receivedObjFormData = this._form.gatherFormValues();

				// prepare the Form, initialize connects
				if (this.moduleFlavor === 'users') {
					this.prepareFormUsers();
				} else if (this.moduleFlavor === 'groups') {
					this.prepareFormGroups();
				}

				this.standby(false);
			}), dojo.hitch(this, function() {
					this.standby(false);
			}));
		},

		confirmClose: function() {
		// summary:
		// 		If changes have been made ask before closing the detailpage
			if (!this._newObject && !umctools.isEqual(this._form.gatherFormValues(), this._receivedObjFormData)) {
				return dialog.confirm( this._('There are unsaved changes. Are you sure to cancel nevertheless?'), [{
					label: this._('Discard changes'),
					name: 'quit',
					callback: dojo.hitch(this, 'onClose')
				}, {
					label: this._('Continue editing'),
					name: 'cancel',
					'default': true
				}]);
			}

			this.onClose();
		},

		onClose: function() {
			// event stub 
		}
	}
});
