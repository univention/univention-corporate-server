/*
 * Copyright 2014-2019 Univention GmbH
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
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/Deferred",
	"dojo/promise/all",
	"umc/tools",
	"umc/dialog",
	"umc/widgets/Page",
	"umc/widgets/Form",
	"umc/widgets/StandbyMixin",
	"umc/widgets/TextBox",
	"umc/widgets/HiddenInput",
	"umc/modules/uvmm/types",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, Deferred, all, tools, dialog, Page, Form, StandbyMixin, TextBox, HiddenInput, types, _) {

	return declare("umc.modules.uvmm.InstancePage", [ Page, StandbyMixin ], {
		nested: true,

		_generalPage: null,

		_instance: null,

		_appendLinkToLabel: function(widget, url) {
			var label = widget.get('label');
			widget.set('label', label + ' ' + lang.replace('<a href="{url}" target="_blank">{text}</a>', {
				'url': url,
				'text': url
			}));
		},

		addNotification: dialog.notify,
		headerText: _('General settings'),

		postMixInProperties: function() {
			this.inherited(arguments);

			this.headerButtons = [{
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Back to overview'),
				callback: lang.hitch(this, 'onClose')
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);
			//
			// general settings page
			//

			this._generalForm = new Form({
				widgets: [{
					name: 'instanceURI',
					type: HiddenInput
				}, {
					name: 'label',
					type: TextBox,
					label: _('Name'),
					size: 'Two',
					disabled: true
				}, {
					name: 'public_ips',
					type: TextBox,
					label: _('Public IP address'),
					disabled: true
				}, {
					name: 'private_ips',
					type: TextBox,
					label: _('Private IP address'),
					disabled: true
				}, {
					name: 'u_size_name',
					type: TextBox,
					label: _('Instance size'),
					disabled: true
				}, {
					name: 'keypair',
					type: TextBox,
					label: _('Keypair'),
					disabled: true
				}, {
					name: 'image',
					type: TextBox,
					label: _('Image'),
					size: 'Two',
					disabled: true
				}, {
					name: 'securitygroup',
					type: TextBox,
					label: _('Security group'),
					disabled: true
				}],
				layout: [{
					label: _('Settings'),
					layout: [
						['label'],
						['image'],
						['public_ips', 'private_ips'],
						['u_size_name', 'keypair'],
						['securitygroup']
					]
				}]
			});
			this.addChild(this._generalForm);
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

					// avoid duplicate public_ips
					var newArr = [];
					array.forEach(this._instance.public_ips, function(item) {
						if(array.indexOf(newArr, item) == -1) {
							newArr.push(item);
						}
					});
					this._instance.public_ips = newArr;

					// set values to form
					this._generalForm.setFormValues(this._instance);

					// append public/private https link
					if (this._instance.public_ips[0]) {
						var widget_public = this._generalForm.getWidget('public_ips');
						this._appendLinkToLabel(widget_public, 'https://' + this._instance.public_ips[0]);
					}
					if (this._instance.private_ips[0]) {
						var widget_private = this._generalForm.getWidget('private_ips');
						this._appendLinkToLabel(widget_private, 'https://' + this._instance.private_ips[0]);
					}

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
