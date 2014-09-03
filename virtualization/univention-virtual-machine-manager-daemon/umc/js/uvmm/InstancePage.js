/*
 * Copyright 2014 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojo/Deferred",
	"dojo/promise/all",
	"dijit/form/MappedTextBox",
	"umc/tools",
	"umc/dialog",
	"umc/store",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TabContainer",
	"umc/widgets/TitlePane",
	"umc/widgets/ExpandingTitlePane",
	"umc/widgets/StandbyMixin",
	"umc/widgets/TextBox",
	"umc/widgets/TextArea",
	"umc/widgets/HiddenInput",
	"umc/widgets/ComboBox",
	"umc/widgets/MultiInput",
	"umc/widgets/CheckBox",
	"umc/widgets/PasswordBox",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Memory, Observable, Deferred, all, MappedTextBox, tools, dialog, store, Page, Form, ContainerWidget, TabContainer, TitlePane, ExpandingTitlePane, StandbyMixin,
	TextBox, TextArea, HiddenInput, ComboBox, MultiInput, CheckBox, PasswordBox, types, _) {

	return declare("umc.modules.uvmm.InstancePage", [ TabContainer, StandbyMixin ], {
		nested: true,

		_generalPage: null,

		_instance: null,

		addNotification: dialog.notify,

		buildRendering: function() {
			this.inherited(arguments);
			//
			// general settings page
			//

			this._generalPage = new Page({
				headerText: _('General settings'),
				title: _('General'),
				footerButtons: [{
					label: _('Back to overview'),
					name: 'cancel',
					callback: lang.hitch(this, 'onClose')
				}, {
					label: _('Save'),
					defaultButton: true,
					name: 'save',
					callback: lang.hitch(this, 'save')
				}]
			});

			this._generalForm = new Form({
				widgets: [{
					name: 'instanceURI',
					type: HiddenInput
				}, {
					name: 'label',
					type: TextBox,
					label: _('Name')
				}],
				layout: [{
					label: _('Settings'),
					layout: [
						'label'
					]
				}],
				scrollable: true
			});
			this._generalForm.on('Submit', lang.hitch(this, 'save'));
			this._generalPage.addChild(this._generalForm);

			// add pages in the correct order
			this.addChild(this._generalPage);
		},

		save: function() {
			// validate
			var valid = true;
			var widgets = lang.mixin({}, this._generalForm._widgets);
			var values = lang.clone(this._instance);
			delete values.instanceURI;
			tools.forIn(widgets, function(iname, iwidget) {
				valid = valid && (false !== iwidget.isValid());
				values[iname] = iwidget.get('value');
				return valid;
			}, this);

			if (!valid) {
				dialog.alert(_('The entered data is not valid. Please correct your input.'));
				return;
			}

			// TODO save values
			console.log('# values: ', values);
			this.onClose();
		},

		load: function(id) {
			// clear form data
			this._generalForm.clearFormValues();

			var deferred = new Deferred();
			deferred.resolve();

			var deferred1 = deferred.then(lang.hitch(this, function() {
				return tools.umcpCommand('uvmm/instance/query', {
					nodePattern: id.slice(0, id.indexOf('#')),
					domainPattern: id.slice(id.indexOf('#') + 1)
				});
			}));

			deferred = all([deferred1]).then(lang.hitch(this, function(data) {
				// get data blob
				this._instance = lang.getObject('0.result.0', false, data); // data[0].result[0]
				this._instance.instanceURI = id;

				if (data) {
					// set title
					this.moduleWidget.set('titleDetail', this._instance.label);

					// set values to form
					this._generalForm.setFormValues(this._instance);

					// deactivate most input field when instance is running
					var active = types.isActive(this._instance);
					if (active) {
						this.addNotification( _( 'While the virtual machine is running most of the settings can not be changed.' ) );
					}

					// name should not be editable
					this._generalForm._widgets.label.set('disabled', true);

					this.selectChild(this._generalPage, true);
				}
			}));
			this.standbyDuring(deferred);
		},

		onClose: function() {
			// event stub
		},

		onUpdateProgress: function(i, n) {
			// event stub
		}
	});
});
