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
	"dijit/Dialog",
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/StandbyMixin",
	"umc/i18n!umc/modules/printers"
], function(declare, lang, Dialog, tools, Form, TextBox, ComboBox, StandbyMixin, _) {
	return declare("umc.modules.printers.QuotaDialog", [ Dialog, StandbyMixin ], {

		buildRendering: function() {

			this.inherited(arguments);

			var buttons = [
				{
					name:			'cancel',
					label:			_("Cancel"),
					// no special meaning of the button name 'cancel', so we
					// have to make a separate callback for this button.
					callback: lang.hitch(this, function() {
						this.onCancel();
					})
				},
				{
					name:			'submit',
					label:			_("Save changes")
					// no callback here: the onSubmit() event of the form
					// will automatically be fired if our button has
					// the name 'submit'
				}
			];

			var widgets = [
				{
					name:				'printer',
					type:				TextBox,
					label:				_("Printer name"),
					disabled:			true
				},
				{
					name:				'user',
					type:				ComboBox,
					label:				_("User name"),
					sortStaticValues:	true,
					required:			true
				},
				{
					name:				'soft',
					type:				TextBox,
					regExp:				'\\d+',
					required:			true,
					label:				_("Soft limit")
				},
				{
					name:				'hard',
					type:				TextBox,
					regExp:				'\\d+',
					required:			true,
					label:				_("Hard limit")
				}
			];

			var layout = [
				[ 'printer' ],
				[ 'user' ],
				[ 'soft' ],
				[ 'hard' ]
			];

			this._form = new Form({
				buttons:		buttons,
				widgets:		widgets,
				layout:			layout,
				onSubmit: lang.hitch(this, function(values) {
					if (this._check_valid('onsubmit'))
					{
						this.onSubmit(this._form.gatherFormValues());
					}
					return false;
				})
			});
			this.set('content',this._form);

			this._form.on('Cancel',lang.hitch(this,function() {
				this.onCancel();
			}));

			// check 'submit' allowance on every field change
			tools.forIn(this._form._widgets, function(wname, wobj) {
				this.own(wobj.watch('value', lang.hitch(this, function() {
					this._check_valid(wname);
				})));
			}, this);

		},

		// checks that all dialog elements are valid, allows
		// or forbids the 'submit' button.
		_check_valid: function(title) {

			var allow = true;
			for (var w in this._form._widgets)
			{
				var wid = this._form._widgets[w];

				if (! wid.isValid())
				{
					allow = false;
					wid.set('state','Error');		// force visibility of state
				}
			}
			this._form._buttons['submit'].setDisabled(! allow);

			return allow;
		},

		onShow: function() {

			this.inherited(arguments);

			// reset all error indicators
			for (var w in this._form._widgets)
			{
				var wid = this._form._widgets[w];
				wid.setValid(null);
			}
			// allow/forbid SUBMIT according to current form contents
			this._check_valid();
		},

		// will be called from QuotaPage just before showing
		// the dialog. the 'values' are now composed from
		// different things:
		//
		//	(1)	initial values for the dialog elements (printer, user, hard, soft)
		//	(2)	the title for the dialog
		//	(3)	the list of users to show in the ComboBox
		//
		setValues: function(values) {

			// for 'add quota entry': set a list of users, excluding those
			// that already have a quota entry
			var userlist = [];
			var entry;

			if (values['users'])
			{
				for (var u in values['users'])
				{
					var un = values['users'][u];
					entry = { id: un, label: un };
					userlist.push(entry);
				}
			}
			// for 'edit quota entry' the 'user' ComboBox is readonly, so it is
			// sufficient to set the list to the one user being edited... this will
			// catch the case where we have an entry for a user that doesn't exist
			// anymore.
			var disabled = false;

			if (values['user'])
			{
				this._work_mode = 'edit';
				entry = { id: values['user'], label: values['users'] };
				userlist.push(entry);
				disabled = true;
			}
			else
			{
				this._work_mode = 'add';
				values['user'] = null;		// force them to touch the ComboBox at least once
			}
			this._form.getWidget('user').set('staticValues',userlist);
			this._form.getWidget('user').setDisabled(disabled);

			if (values['title'])
			{
				this.set('title',values['title']);
			}

			this._form.setFormValues(values);
		},

		// event stubs for our caller
		onSubmit: function(values) {
			this.hide();
		},

		onCancel: function() {
			this.hide();
		}
	});
});
