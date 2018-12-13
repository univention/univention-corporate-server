/*
 * Copyright 2011-2019 Univention GmbH
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
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/PasswordBox",
	"umc/i18n!umc/modules/join"
], function(declare, lang, tools, Form, Text, TextBox, PasswordBox, _) {

	return declare("umc.modules.join.Form", [ Form ], {
		constructor: function() {
			this.buttons = [{
				name:			'submit',
				label:			_("Join system")
			}];

			this.widgets = [{
				type:			TextBox,
				name:			'username',
				value:			tools.status('username') == 'root' ? 'Administrator' : tools.status('username'),
				label:			_('Username'),
				description:	_('The username of the domain administrator')
			}, {
				type:			PasswordBox,
				name:			'password',
				value:			'',
				label:			_( 'Password' ),
				description:	_( 'Password of the domain administrator' )
			}, {
				type:			TextBox,
				name:			'hostname',
				value:			'',
				label:			_('Hostname of domain controller master'),
				description:	_('The hostname of the domain controller master of the domain')
			}, {
				type:			Text,
				name:			'warning',
				style:			'margin-bottom: 1em;',
				content:		'',
				visible:		false
			}];

		},

		buildRendering: function() {
			this.inherited(arguments);

			tools.umcpCommand('join/master').then(lang.hitch(this, function(data) {
				// guess the master hostname
				if (data.result.master) {
					this._widgets.hostname.set('value', data.result.master);
				} else if (data.result.error_message) {
					//notify user in case of a dns lookup error
					var networkLink = tools.linkToModule({module: 'setup', flavor: 'network'});
					var _warningMessage = lang.replace('<b>{0}</b>{1} {2}', [
						_('Warning: '), data.result.error_message,
						// i18n: %s is the "Network settings module".
						networkLink ? _('The DNS settings can be adjusted in the %s.', networkLink) : ''
					]);
					this._widgets.warning.set('content', _warningMessage);
					this._widgets.warning.set('visible', true);
				}
			}));
		}
	});
});
