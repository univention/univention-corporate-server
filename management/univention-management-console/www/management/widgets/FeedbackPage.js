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
	"dojo/_base/lang",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/CheckBox",
	"umc/i18n!management"
], function(lang, tools, Text, CheckBox, _) {
	return {
		name: 'feedback',
		headerText: _('Feedback via usage statistics'),
		'class': 'umcAppDialogPage umcAppDialogPage-feedback',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text',
			content: _('<p>On UCS evaluation systems, anonymous usage statistics are created by default and sent to Univention. This allows to continuously adapt UCS to suit the practical needs of its users.</p><p>The information consists of UMC usage statistics and a one-time statistic on the hardware configuration. Details about the usage statistics and about its deactivation can be found in the <a href="https://docs.software-univention.de/manual-%(version)s.html#central-management-umc:piwik" target="_blank">UCS manual</a>.</p><p>Usage statistics are automatically deactivated when importing a commercial license.</p>', {
				version: tools.status('ucsVersion').split('-')[0]
			})
		}, {
			type: CheckBox,
			visible: false,
			name: 'enableHardwareStatistics',
			label: _('Enable one-time statistic on hardware configuration.'),
			value: true
		}]
	};
});
