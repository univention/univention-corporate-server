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
	"umc/dialog",
	"umc/widgets/Form",
	"umc/widgets/Page",
	"umc/widgets/TextBox",
	"umc/widgets/ComboBox",
	"umc/widgets/StandbyMixin",
	"umc/i18n!umc/modules/MODULEID"
], function(declare, lang, dialog, Form, Page, TextBox, ComboBox, StandbyMixin, _) {
	return declare("umc.modules.MODULEID.DetailPage", [ Page, StandbyMixin ], {
		// summary:
		//		This class represents the detail view of our dummy module.

		// reference to the module's store object
		moduleStore: null,

		// internal reference to the formular containing all form widgets of an UDM object
		_form: null,

		// Set the opacity for the standby animation to 100% in order to mask
		// GUI changes when the module is opened. Call this.standby(true|false)
		// to enabled/disable the animation.
		standbyOpacity: 1,

		postMixInProperties: function() {
			// is called after all inherited properties/methods have been mixed
			// into the object (originates from dijit._Widget)

			// it is important to call the parent's postMixInProperties() method
			this.inherited(arguments);

			// set the page header
			this.headerText = _('Object properties');
			this.helpText = _('This page demonstrates how object properties can be viewed for editing.');

			// configure buttons for the header of the detail page
			this.headerButtons = [{
				name: 'submit',
				label: _('Save'),
				iconClass: 'umcSaveIconWhite',
				callback: lang.hitch(this, function() {
					this._save(this._form.get('value'));
				})
			}, {
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Back to overview'),
				callback: lang.hitch(this, 'onClose')
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
				type: TextBox,
				name: 'id',
				label: _('Identifier'),
				disabled: true
			}, {
				type: TextBox,
				name: 'name',
				label: _('Displayed name'),
				description: _('Name that is displayed')
			}, {
				type: ComboBox,
				name: 'color',
				label: _('Favorite color'),
				description: _('Favorite color associated with the current entry'),
				dynamicValues: 'MODULEID/colors'
			}];

			// specify the layout... additional dicts are used to group form elements
			// together into title panes
			var layout = [{
				label: _('Read-only properties'),
				layout: [ 'id' ]
			}, {
				label: _('Editable properties'),
				layout: [ 'name', 'color' ]
			}];

			// create the form
			this._form = new Form({
				widgets: widgets,
				layout: layout,
				moduleStore: this.moduleStore
			});

			// add form to page...
			this.addChild(this._form);

			// hook to onSubmit event of the form
			this._form.on('submit', lang.hitch(this, '_save'));
		},

		_save: function(values) {
			dialog.alert(_('Feature not implemented yet!'));
		},

		load: function(id) {
			// during loading show the standby animation
			this.standby(true);

			// load the object into the form... the load method returns a
			// Deferred object in order to handel asynchronity
			this._form.load(id).then(lang.hitch(this, function() {
				// done, switch of the standby animation
				this.standby(false);
			}), lang.hitch(this, function() {
				// error handler: switch of the standby animation
				// error messages will be displayed automatically
				this.standby(false);
			}));
		},

		onClose: function() {
			// event stub
		}
	});
});
