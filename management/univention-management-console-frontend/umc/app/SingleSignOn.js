/*
 * Copyright 2015 Univention GmbH
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
/*global define window*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/request/xhr",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/i18n!",
	"dojo/domReady!",
	"dojo/NodeList-dom"
], function(declare, lang, xhr, ContainerWidget, Button, _) {
	return declare('umc.app.SingleSignOn', [ContainerWidget], {
		_languageMenu: null,
		_languageButton: null,

		sso_uri: '/univention-management-console/saml/',

		postMixInProperties: function() {
			this.ssoButton = new Button({
				label: _('Single Sign On'),
				iconClass: 'umcPlayIcon',
				description: _('Single Sign On allows a user to login once and access multiple applications seamlessly. For a safe implementation, it is necessary that the names of the involved systems can be reached via DNS by the web browser.'),
				callback: lang.hitch(this, function() {
					window.location = this.sso_uri;
				})
			});
			xhr.get('/univention-management-console/entries.json', {handleAs: 'json'}).always(lang.hitch(this, function(result) {
				var uri = window.location.protocol + '//' + result.ucr['ucs/server/sso/fqdn'] + '/simplesamlphp/blank.json';
				return xhr.get(uri, {handleAs: 'json', timeout: 3000}).then(function(res) {
					if (res.status == 200) {
						return true;
					}
					throw new Error('IDP is not reachable!');
				});
			})).otherwise(lang.hitch(this, function() {
				this.sso_uri = _('http://sdb.univention.de/1351');
				this.ssoButton.set('label', '<s>' + this.ssoButton.get('label') + '</s>');
			}));
		},
		buildRendering: function() {
			this.inherited(arguments);
			this.addChild(this.ssoButton);
		}
	});
});
