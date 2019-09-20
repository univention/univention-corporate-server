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
	"umc/widgets/TextBox",
	"umc/i18n!management"
], function(lang, tools, Text, TextBox, _) {
	var pageConf = {
		name: 'activation',
		headerText: _('Activation of Univention Corporate Server'),
		'class': 'umcAppDialogPage umcAppDialogPage-activation',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text',
			content: _('<p>You may now enter a valid e-mail address in order to activate the UCS system to use the App Center. In the next step you can upload the license file that has been sent to your email address.</p>')
		}, {
			type: TextBox,
			name: 'email',
			inlineLabel: _('E-mail address'),
			regExp: '.+@.+',
			invalidMessage: _('No valid e-mail address.'),
			size: 'Two'
		}, {
			type: Text,
			name: 'text2',
			labelConf: {
				'class': 'umcActivationLeaveFieldFreeMessage'
			},
			content: _('<p>Leave the field empty to perform the activation at a later point in time via the user menu in top right corner.</p>')
		}, {
			type: Text,
			name: 'text3',
			content: _('<p>Details about the activation of a UCS license can be found in the <a href="https://docs.software-univention.de/manual-%(version)s.html#central:license" target="_blank">UCS manual</a>.</p>', {
				version: tools.status('ucsVersion').split('-')[0]
			})
		}]
	};

	var _ucrDeferred = null;
	var ucr = function() {
		if (!_ucrDeferred) {
			_ucrDeferred = tools.ucr(['uuid/license', 'ucs/web/license/requested']).then(function(ucr) {
				var res = {
					hasLicense: Boolean(ucr['uuid/license']),
					hasLicenseRequested: tools.isTrue(ucr['ucs/web/license/requested'])
				};
				res.showInStartupDialog = !res.hasLicense && !res.hasLicenseRequested;
				return res;
			});
		}
		return _ucrDeferred;
	};

	// return an AMD plugin that resolves when the UCR variables have been loaded
	return {
		load: function (params, req, load, config) {
			ucr().then(function(info) {
				load(lang.mixin({}, info, pageConf));
			});
		}
	};
});
