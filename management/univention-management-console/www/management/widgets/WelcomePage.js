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
	"dojo/query",
	"dojo/dom-class",
	"dijit/registry",
	"umc/widgets/Text",
	"umc/widgets/RadioButton",
	"umc/i18n!management"
], function(declare, query, domClass, registry, Text, RadioButton, _) {
	var _RadioButton = declare(RadioButton, {
		_setCheckedAttr: function(value) {
			this.inherited(arguments);
			var result = query('.umcAppWelcomePageLink').forEach(function(inode) {
				domClass.toggle(inode, 'dijitDisplayNone', !value);
			});
		}
	});

	return {
		name: 'welcome',
		headerText: _('Welcome to Univention Management Console'),
		'class': 'umcAppDialogPage umcAppDialogPage-welcome',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text',
			content: _('<p>Congratulations, you have successfully completed the configuration of your Univention Corporate Server (UCS), and you have logged into Univention Management Console (UMC). UMC is the central web application for a comfortable system administration and domain management.</p><p>Are you satisfied with the system configuration?</p>')
		}, {
			type: RadioButton,
			name: 'installation_ok',
			label: _('Everything worked great.'),
			radioButtonGroup: 'umcStartupWelcomePageRadioButtons',
			isValid: function() {
				return true;
			}
		}, {
			type: _RadioButton,
			name: 'installation_not_ok',
			label: _('I see potential for improvement.'),
			radioButtonGroup: 'umcStartupWelcomePageRadioButtons',
			isValid: function() {
				return true;
			}
		}, {
			type: Text,
			name: 'link',
			content: _('<p><a href="%s?umc=StartupDialog" target="_blank">Tell us your opinion!</a></p>', _('https://www.univention.com/feedback/')),
			labelConf: {
				'class': 'umcAppWelcomePageLink dijitDisplayNone'
			}
		}]
	};
});
