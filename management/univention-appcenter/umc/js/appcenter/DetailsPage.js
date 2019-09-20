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
	"dojox/html/entities",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/CheckBox",
	"umc/widgets/TextBox",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, entities, Page, Form, CheckBox, TextBox, _) {
	return declare("umc.modules.appcenter.DetailsPage", [ Page ], {
		moduleStore: null,
		standby: null, // parents standby method must be passed. weird IE-Bug (#29587)
		headerTextAllowHTML: false,
		helpTextAllowHTML: false,

		postMixInProperties: function() {
			this.inherited(arguments);

			lang.mixin(this, {
				title: _("Components"),
				headerButtons: [{
					name: 'close',
					label: _("Back to overview"),
					callback: lang.hitch(this, function() {
						try {
							this.onCloseDetail();
						} catch(error) {
							console.error("onCancel: " + error.message);
						}
					})
				}, {
					name: 'submit',
					'default': true,
					label: _("Apply changes"),
					callback: lang.hitch(this, function() {
						this._form.onSubmit();
					})
				}]
			});
		},

		buildRendering: function() {

			this.inherited(arguments);

			var widgets = [
				{
					type: CheckBox,
					name: 'enabled',
					label: _("Enable this component")
				},
				{
					type: TextBox,
					name: 'name',
					label: _("Component name")
				},
				{
					type: TextBox,
					name: 'description',
					label: _("Description")
				},
				{
					type: TextBox,
					name: 'server',
					label: _("Repository server")
				},
				{
					type: TextBox,
					name: 'prefix',
					label: _("Repository prefix")
				},
				{
					type: CheckBox,
					name: 'unmaintained',
					label: _("Use unmaintained repositories")
				},
				{
					type: TextBox,
					name: 'username',
					label: _("Username")
				},
				{
					type: TextBox,
					name: 'password',
					label: _("Password")
				},
				{
					type: TextBox,
					name: 'version',
					label: _("Version"),
					regExp: '^((([0-9]+\\.[0-9]+|current),)*([0-9]+\\.[0-9]+|current))?$'
				}
			];

			var layout =
			[
				{
					label: _("Basic settings"),
					layout:
					[
						['enabled'],
						['name', 'description'],
						['server', 'prefix']
					]
				},
				{
					label: _("Advanced settings"),
					layout:
					[
						['unmaintained'],
						['username', 'password'],
						['version']
					]
				}
			];

			this._form = new Form({
				widgets: widgets,
				layout: layout,
				//buttons: buttons,
				moduleStore: this.moduleStore
			});
			this.addChild(this._form);

			// the onSubmit event should not be overwritten, instead connect should
			// be used (see Bug #25093)
			this._form.on('submit', lang.hitch(this, function() {
				this.standby(true);
				this._form.save();
			}));

			this._form.on('saved', lang.hitch(this, function(success) {
				this.standby(false);
				try {
					if (success) {
						this.onCloseDetail();
					}
				} catch(error) {
					console.error("DetailsPage.onSaved: " + error.message);
				}
			}));
		},

		// Entry point for opening the edit page. API now changed, so the detail knowledge
		// is not in this page:
		//
		//	isnew ..... true -> we're adding, false -> we're editing
		//	data ...... if EDIT: the id of the record to load
		//				if ADD: a dict of default values
		startEdit: function(isnew, data) {
			if (isnew) {
				this.set('headerText', _("Add a new component"));
				this.set('helpText', _("Please enter the details for the new component."));

				this._form.setFormValues(data);
				this.standby(false);

				// Component name editable and focused?
				var name = this._form.getWidget('name');
				if (name) {
					name.set('disabled', false);
					name.focus();
				}
			} else {
				this.set('headerText', lang.replace(_("Edit component details [{component}]"), {component: data}));
				this.set('helpText', _("You're editing the details of the component definition."));

				this._form.load(data).then(lang.hitch(this, function() { this.standby(false); }));

				// If we are in EDIT mode: do not allow changes to the component name.
				this._form.getWidget('name').set('disabled', true);

				// let us suppose the SERVER field is a good focus start
				this._form.getWidget('server').focus();
			}
		},

		// return to grid view
		onCloseDetail: function() {
		},

		// Returns defaults for a new component definition.
		getComponentDefaults: function() {

				return ({
					// Behavior: enable the component in first place
					enabled: true,
					// Empty fields
					name: '',
					description: '',
					prefix: '',
					username: '',
					password: '',
					defaultpackages: '',
					server: '',
					// TODO These have to be copied from the current settings
					unmaintained: false
				});
		}

	});
});
