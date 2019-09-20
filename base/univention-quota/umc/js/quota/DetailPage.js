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
	"dojo/_base/array",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/TextBox",
	"umc/widgets/Page",
	"umc/widgets/NumberSpinner",
	"umc/i18n!umc/modules/quota"
], function(declare, lang, array, dialog, tools, Form, TextBox,  Page, NumberSpinner, _) {

	return declare("umc.modules.quota.DetailPage", [ Page ], {

		partitionDevice: null,
		standby: null,
		standbyDuring: null,
		_form: null,

		buildRendering: function() {
			this.inherited(arguments);
			this.renderForm();

			this.addChild(this._form);
		},

		postMixInProperties: function() {
			this.inherited(arguments);
			this.headerButtons = [{
				name: 'close',
				iconClass: 'umcCloseIconWhite',
				label: _('Back to partition'),
				callback: lang.hitch(this, 'onClosePage')
			}, {
				name: 'submit',
				iconClass: 'umcSaveIconWhite',
				label: _('Save changes'),
				callback: lang.hitch(this, function() {
					if (this.validateValues()) {
						var values = this._form.get('value');
						this.onSetQuota(values);
					}
				})
			}];
		},

		postCreate: function() {
			this.inherited(arguments);
			this.startup();
		},

		renderForm: function() {
			var widgets = [{
				type: TextBox,
				name: 'user',
				label: _('User'),
				required: true
			}, {
				type: TextBox,
				name: 'partitionDevice',
				label: _('Partition'),
				value: this.partitionDevice,
				disabled: true
			}, {
				type: NumberSpinner,
				name: 'sizeLimitSoft',
				label: _('Data size soft limit (MB)'),
				value: 0,
				smallDelta: 10,
				largeDelta: 100,
				constraints: {
					min: 0
				}
			}, {
				type: NumberSpinner,
				name: 'sizeLimitHard',
				label: _('Data size hard limit (MB)'),
				value: 0,
				smallDelta: 10,
				largeDelta: 100,
				constraints: {
					min: 0
				}
			}, {
				type: NumberSpinner,
				name: 'fileLimitSoft',
				label: _('Files soft limit'),
				value: 0,
				smallDelta: 10,
				largeDelta: 100,
				constraints: {
					min: 0
				}
			}, {
				type: NumberSpinner,
				name: 'fileLimitHard',
				label: _('Files hard limit'),
				value: 0,
				smallDelta: 10,
				largeDelta: 100,
				constraints: {
					min: 0
				}
			}];

			var layout = [['user', 'partitionDevice'], ['sizeLimitSoft', 'sizeLimitHard'], ['fileLimitSoft', 'fileLimitHard']];

			this._form = new Form({
				region: 'main',
				widgets: widgets,
				layout: layout
			});
		},

		onClosePage: function() {
			return true;
		},

		onSetQuota: function(values) {
			return true;
		},

		init: function(userQuota) {
			if (userQuota === undefined) {
				this._form.clearFormValues();
				this._form.getWidget('user').set('disabled', false);
				this.set('headerText', _('Add quota'));
				this.set('helpText', _('Add quota settings for a new user on partition <i>%s</i>.', this.partitionDevice));
			}
			else {
				this._form.setFormValues(userQuota);
				this._form.getWidget('user').set('disabled', true);
				this.set('headerText', _('Modify quota'));
				this.set('helpText', _('Modify the quota settings for user <i>%(user)s</i> on partition <i>%(partition)s</i>.', {user: userQuota.user, partition: userQuota.partitionDevice}));
			}
			this._form.getWidget('partitionDevice').setValue(this.partitionDevice);
		},

		validateValues: function() {
			// check whether the username is specified
			if (this._form.getWidget('user').get('value') === '') {
				dialog.alert(_('A username needs to be specified.'));
				return false;
			}

			// make sure that not all values are set to zero
			var quotaValues = ['sizeLimitSoft', 'sizeLimitHard', 'fileLimitSoft', 'fileLimitHard'];
			var zeroValues = array.filter(quotaValues, lang.hitch(this, function(ikey) {
				return this._form.getWidget(ikey).get('value') <= 0;
			}));
			if (quotaValues.length == zeroValues.length) {
				dialog.alert(_('Not all limits can be set to zero.'));
				return false;
			}

			var sizeLimitSoft = this._form.getWidget('sizeLimitSoft').get('value');
			var sizeLimitHard = this._form.getWidget('sizeLimitHard').get('value');
			var fileLimitSoft = this._form.getWidget('fileLimitSoft').get('value');
			var fileLimitHard = this._form.getWidget('fileLimitHard').get('value');
			if (sizeLimitHard < sizeLimitSoft || fileLimitHard < fileLimitSoft) {
				dialog.alert(_('The soft limit needs to be less than or equal to the hard limit'));
				return false;
			}
			return true;
		}
	});
});
