/*
 * Copyright 2013-2019 Univention GmbH
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
	"dijit/Dialog",
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/ComboBox",
	"umc/widgets/Form",
	"umc/widgets/HiddenInput",
	"umc/widgets/NumberSpinner",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/i18n!umc/modules/firewall"
], function(Dialog, declare, lang, dlg, tools, ComboBox, Form, HiddenInput,
            NumberSpinner, StandbyMixin, Text, TextBox, _) {
	return declare("umc.modules.firewall", [Dialog, StandbyMixin], {

		moduleStore: null,

		_form: null,

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: ComboBox,
				name: 'protocol',
				label: _('Protocol'),
				staticValues: [{
					id: 'tcp',
					label: _('TCP')
				}, {
					id: 'udp',
					label: _('UDP')
				}]
			}, {
				type: NumberSpinner,
				name: 'portStart',
				label: _('Port start'),
				value: 1,
				constraints: {
					min: 1,
					max: 65535,
					pattern: '#'
				},
				onChange: lang.hitch(this, '_updatePortEnd')
			}, {
				type: NumberSpinner,
				name: 'portEnd',
				label: _('Port end'),
				value: 1,
				constraints: {
					min: 1,
					max: 65535,
					pattern: '#'
				}
			}, {
				type: ComboBox,
				name: 'addressType',
				label: _('Address type'),
				staticValues: [{
					id: 'all',
					label: _('All addresses')
				}, {
					id: 'ipv4',
					label: _('All IPv4 addresses')
				}, {
					id: 'ipv6',
					label: _('All IPv6 addresses')
				}, {
					id: 'specific',
					label: _('Specific address')
				}],
				onChange: lang.hitch(this, '_updateAddressValue')
			}, {
				type: TextBox,
				name: 'addressValue',
				label: _('Local address')
			}, {
				type: ComboBox,
				name: 'action',
				label: _('Action'),
				staticValues: [{
					id: 'accept',
					label: _('ACCEPT')
				}, {
					id: 'reject',
					label: _('REJECT')
				}, {
					id: 'drop',
					label: _('DROP')
				}]
			}, {
				type: Text,
				name: 'descriptionText',
				label: _('Description'),
				style: 'margin-bottom: 5px'
			}, {
				type: HiddenInput,
				name: 'description'
			}];

			var buttons = [{
				name: 'submit',
				label: _('Create'),
				style: 'float:right;',
				callback: lang.hitch(this, 'save')
			}, {
				name: 'cancel',
				label: _('Cancel'),
				callback: lang.hitch(this, function() {
					this.hide();
				})
			}];

			var layout = [['protocol'], 
			              ['portStart', 'portEnd'],
			              ['addressType', 'addressValue'],
			              ['action'],
			              ['descriptionText']];

			this._form = this.own(new Form({
				style: 'width: 100%',
				widgets: widgets,
				buttons: buttons,
				layout: layout,
				moduleStore: this.moduleStore
			}))[0];
			this._form.placeAt(this.containerNode);

			// simple handler to disable standby mode
			this._form.on('loaded', lang.hitch(this, function() {
				// display the description text
				var widget = this._form.getWidget('descriptionText');
				var text = this._form.getWidget('description').get('value');
				if (text) {
					// we have description, update the description field
					widget.set('visible', true);
					widget.set('content', '<i>' + text + '</i>');
				}
				else {
					// no description -> hide widget and label
					widget.set('visible', false);
					widget.set('content', '');
				}
				this.standby(false);
			}));
		},

		_updatePortEnd: function() {
			var portStart = this._form.getWidget('portStart').get('value');
			var portEnd = this._form.getWidget('portEnd').get('value');
			if (portStart > portEnd) {
				this._form.getWidget('portEnd').set('value', portStart);
			}
		},

		_updateAddressValue: function(type) {
			var widget = this._form.getWidget('addressValue');
			if (type === 'specific') {
				widget.set('disabled', false);
			} else {
				widget.set('value', '');
				widget.set('disabled', true);
			}
		},

		save: function() {
			this.standby(true);
			this._updatePortEnd();
			this._form.save().then(lang.hitch(this, function(result) {
				this.standby(false);
				if (! result.success) {
					dlg.alert(result.details);
				} else {
					this.hide()
				}
			}), lang.hitch(this, function() {
				this.standby(false);
			}))
		},

		clearForm: function() {
			tools.forIn(this._form._widgets, function(name, widget) {
				if (name === 'descriptionText') {
					return;
				}
				widget.reset()
				widget.setValid(true);
			});
			var addressType = this._form.getWidget('addressType').get('value');
			this._updateAddressValue(addressType);
			this._form._loadedID = null;
		},

		newRule: function() {
			this.clearForm();
			this._form.getWidget('descriptionText').set('visible', false);
			this.set('title', _('Create new firewall rule'));
			this._form.getButton('submit').set('label', _('Create'));
			this.show();
		},

		editRule: function(identifier) {
			this.clearForm();
			this.standby(true);
			this.show();

			this._form.load(identifier);
			this.set('title', _('Edit existing firewall rule'));
			this._form.getButton('submit').set('label', _('Save'));
		}
	});
});
