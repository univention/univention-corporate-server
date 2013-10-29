/*
 * Copyright 2011-2013 Univention GmbH
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
				type:			Text,
				name:			'text',
				style:			'margin-bottom:1em;',
				content:		_("Please enter credentials of a user account with administrator rights to join the system.")
			}, {
				type:			TextBox,
				name:			'username',
				value:			tools.status('username'),
				label:			_('Username'),
				description:	_('The username of the domain administrator')
			}, {
				type:			PasswordBox,
				name:			'password',
				value:			'',
				label: 			_( 'Password' ),
				description:	_( 'Password of the domain administrator' )
			}, {
				type:			TextBox,
				name:			'hostname',
				value:			'',
				label:			_('Hostname of domain controller master'),
				description:	_('The hostname of the domain controller master of the domain')
			}];
		},

		buildRendering: function() {
			this.inherited(arguments);
			tools.umcpCommand('join/master').then(lang.hitch(this, function(data) {
				// guess the master hostname
				this._widgets.hostname.set('value', data.result);
			}));
		}
	});
});
