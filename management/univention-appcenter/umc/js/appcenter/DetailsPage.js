/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2011-2024 Univention GmbH
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
	"dojo/dom-class",
	"dojox/html/entities",
	"umc/dialog",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/CheckBox",
	"umc/widgets/TextBox",
	"umc/i18n!umc/modules/appcenter"
], function(declare, lang, domClass, entities, dialog, Page, Form, CheckBox, TextBox, _) {
	return declare("umc.modules.appcenter.DetailsPage", [ Page ], {
		moduleStore: null,
		standby: null, // parents standby method must be passed. weird IE-Bug (#29587)
		headerTextAllowHTML: false,
		helpTextAllowHTML: false,
		navContentClass: 'umcCard2',

		postMixInProperties: function() {
			this.inherited(arguments);

			lang.mixin(this, {
				title: _("Components"),
				headerButtons: [{
					name: 'close',
					label: _("Back to overview"),
					callback: lang.hitch(this, function() {
						try {
							this.onCloseDetail(0);
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
			domClass.add(this.domNode, 'umcAppCenterRepositoryDetailsPage');

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
					label: _("Repository server"),
					size: 'Two'
				},
				{
					type: TextBox,
					name: 'version',
					label: _("Version"),
					regExp: '^((([0-9]+\\.[0-9]+|current),)*([0-9]+\\.[0-9]+|current))?$'
				},
				{
					type: CheckBox,
					name: 'unmaintained',
					label: _("Use unmaintained repositories")
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
						['server']
					]
				},
				{
					label: _("Advanced settings"),
					layout:
					[
						['version', 'unmaintained']
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
				this._form.save().then(lang.hitch(this, function(data) {this.standby(false); this.onCloseDetail(data); }));
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
		onCloseDetail: function(data) {
			var result = data;
			if (data instanceof Array) {
				result = data[0];
			}

			if (!(result.status && result.message)) {
				return;
			}

			// result['status'] is kind of error code:
			//	1 ... invalid field input
			//	2 ... error setting registry variable
			//	3 ... error committing UCR
			//	4 ... any kind of 'repo not found' conditions
			//	5 ... repo not found, but encountered without commit
			var txt = _("An unknown error with code %d occurred.", result.status);
			switch(result.status) {
				case 1: txt = _("Please correct the corresponding input fields.");
						break;
				case 2:
				case 3: txt = _("The data you entered could not be saved correctly.");
						break;
				case 4: txt = _("Using the data you entered, no valid repository could be found.<br/>Since this may be a temporary server problem as well, your data was saved though.<br/>The problem was:");
						break;
				case 5: txt = _("With the current (already changed) settings, the following problem was encountered:");
						break;
			}

			var message = lang.replace('<p>{txt}</p><p><strong>{msg}</strong></p>', {txt : txt, msg : result.message});
			dialog.alert(message);
		},

		// Returns defaults for a new component definition.
		getComponentDefaults: function() {

				return ({
					// Behavior: enable the component in first place
					enabled: true,
					// Empty fields
					name: '',
					description: '',
					server: '',
					unmaintained: false
					// TODO These have to be copied from the current settings
				});
		}

	});
});
