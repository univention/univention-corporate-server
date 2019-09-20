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
/*global define*/

define([
	"dojo/_base/declare",
	"umc/widgets/ComboBox",
	"umc/widgets/TextBox",
	"umc/widgets/HiddenInput",
	"umc/widgets/PasswordBox",
	"umc/modules/uvmm/CloudConnectionWizard",
	"umc/i18n!umc/modules/uvmm"
], function(declare,
	ComboBox, TextBox, HiddenInput, PasswordBox, CloudConnectionWizard, _) {
	return declare('umc.modules.uvmm.EC2', [CloudConnectionWizard], {
		postMixInProperties: function() {
			this.inherited(arguments);
			this.pages = [{
				name: 'credentials',
				headerText: _('Create a new cloud connection.'),
				helpText: _('Please enter the corresponding credentials for the cloud connection. <a href="https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSGettingStartedGuide/AWSCredentials.html" target=_blank>Use this link to get information about AWS credentials</a>'),
				layout: [
					'name',
					'region',
					'access_id',
					'password',
					'search_pattern'
				],
				widgets: [{
					name: 'name',
					type: TextBox,
					label: _('Name'),
					required: true
				}, {
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
						{ id: 'EC2_EU_WEST', label: 'EU West (Ireland)' },
						{ id: 'EC2_EU_CENTRAL', label: 'EU Central (Frankfurt)' },
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
				}, {/*
					name: 'ucs_images',
					type: CheckBox,
					value: true
				}, {*/
					name: 'search_pattern',
					type: TextBox,
					value: '',
					label: _('Search pattern for AMIs'),
					description: _('Optional. By default, all UCS images are shown when creating a new cloud instance. If a search pattern is specified, AMIs matching this pattern are also available. "*" finds all images, but the list of available AMIs may get very long and take a considerable amount of time to load.')
				}, {
					name: 'cloudtype',
					type: HiddenInput,
					value: this.cloudtype
				}]
			}];
		}
	});
});
