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
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/i18n!"
], function(tools, Text, TextBox, _) {
	var pageConf = {
		name: 'activation',
		headerText: _('Activation of Univention Corporate Server'),
		'class': 'umcAppDialogPage umcAppDialogPage-activation',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text',
			content: _('<p>You may now enter a valid e-mail address in order to activate the UCS system to use the App Center. Within a short time, you will receive an updated license key. This key can then be uploaded via the license dialog in the settings menu (on the top right).</p>')
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
			content: _('<p>Leave the field empty to perform the activation at a later point in time via the settings menu.</p>')
		}, {
			type: Text,
			name: 'text3',
			content: _('<p>Details about the activation of a UCS license can be found in the <a href="http://docs.univention.de/manual-%(version)s.html#software:appcenter" target="_blank">UCS manual</a>.</p>', {
				version: tools.status('ucsVersion').split('-')[0]
			})
		}]
	};

	var _isLicenseActivatedDeferred = null;
	var isLicenseActivated = function() {
		if (!_isLicenseActivatedDeferred) {
			_isLicenseActivatedDeferred = tools.ucr(['uuid/license', 'ucs/web/license/requested']).then(function(ucr) {
				return Boolean(ucr['uuid/license']) || tools.isTrue(ucr['ucs/web/license/requested']);
			});
		}
		return _isLicenseActivatedDeferred;
	};

	// return an AMD plugin that resolves when the UCR variables have been loaded
	return {
		load: function (params, req, load, config) {
			isLicenseActivated().then(function(activated) {
				load(activated ? null : pageConf);
			});
		}
	};
});
