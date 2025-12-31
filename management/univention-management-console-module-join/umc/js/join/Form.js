/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
				label:			_('Hostname of Primary Directory Node'),
				description:	_('The hostname of the Primary Directory Node of the domain')
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
