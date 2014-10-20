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
	"umc/widgets/TextBox",
	"umc/widgets/PasswordBox",
	"umc/widgets/ComboBox",
	"umc/widgets/CheckBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/Wizard",
	"umc/widgets/Form",
	"umc/i18n!umc/modules/uvmm"
], function(declare, lang, array, TextBox, PasswordBox, ComboBox, CheckBox, HiddenInput, Wizard, Form, _) {

	return declare("umc.modules.uvmm.CloudConnectionWizard", [ Wizard ], {
		autoValidate: true,

		constructor: function(props, cloudtype) {
			this.inherited(arguments);
			this.cloudtype = cloudtype;
		},

		_invalidUrlMessage: _('The url is invalid!<br/>Expected format is: <i>http(s)://</i>'),
		_validateUrl: function(url) {
			url = url || '';
			var _regUrl = /^(http|https)+:\/\//;
			var isUrl = _regUrl.test(url);
			var acceptEmtpy = !url && !this.required;
			return acceptEmtpy || isUrl;
		},

		_getWidgets: function(cloudtype) {
			if (cloudtype == 'EC2') {
				return {
					layout: [
						'region',
						'access_id',
						'password',
						'secure'
					],
					widgets: [{
						name: 'access_id',
						type: TextBox,
						label: _('Access Key ID'),
						required: true
					}, {
						name: 'password',
						type: PasswordBox,
						label: _('Secret Access Key'),
						required: true
					}, {
						name: 'region',
						type: ComboBox,
						staticValues: [
							{ id: 'EC2_EU_WEST', label: 'EU (Ireland)' },
							{ id: 'EC2_US_EAST', label: 'US East (N. Virginia)' },
							{ id: 'EC2_US_WEST', label: 'US West (N. California)' },
							{ id: 'EC2_US_WEST_OREGON', label: 'US West (Oregon)' },
							{ id: 'EC2_AP_SOUTHEAST', label: 'Asia Pacific (Sydney)' },
							{ id: 'EC2_AP_NORTHEAST', label: 'Asia Pacific (Tokyo)' },
							{ id: 'EC2_AP_SOUTHEAST2', label: 'Asia Pacific (Singapore)' },
							{ id: 'EC2_SA_EAST', label: 'South America (São Paulo)' }
						],
						label: _('EC2 Region'),
						required: true
					}, {
						name: 'secure',
						type: CheckBox,
						label: _('Secure connection'),
						value: true,
						required: false
					} ]
				};
			}
			return {};
		},

		_finish: function(pageName) {
			this.inherited(arguments);
		},
		
		onFinished: function() {
			// event stub
		}
	});
});
