/*
 * Copyright 2014-2018 Univention GmbH
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
	"dojo/topic",
	"umc/widgets/Text",
	"dijit/layout/ContentPane",
	"put-selector/put",
	"umc/i18n!management"
], function(topic, Text, ContentPane, put, _) {
	return {

		name: 'help',
		headerText: _('Further Information'),
		'class': 'umcAppDialogPage umcAppDialogPage-help',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text',
			content: _('<p>You can find detailed information on how to use UMC for specific scenarios in the UCS manual. We have linked the most frequent ones of them here:</p>')
		}, {
			type: ContentPane,
			name: 'links2',
			content: (function() {
				var _openPageWithTracking = function(url, key) {
						topic.publish('/umc/actions', 'startup-wizard-exp', 'help', key);
						var w = window.open(url);
						w.focus();
				}

				var ul = put('ul');

				var manual = put('a', {
					href: _('https://docs.univention.de/en/ucs.html'), // have correct link in href for browser support, but ignore via onclick: evt.preventDefault()
					target: '_blank',
					onmousedown: function(evt) {
						evt.preventDefault();
						_openPageWithTracking(this.href, 'ucs-manual');
					},
					innerHTML: _('UCS manual')
				});
				var win_domainjoin = put('a', {
						href: _('https://docs.software-univention.de/quickstart-en-4.3.html#quickstart:clients'),
						target: '_blank',
						onmousedown: function(evt) {
						evt.preventDefault();
						_openPageWithTracking(this.href, 'win_domainjoin');
					},
					innerHTML: _('Join a Windows 10 client into a UCS domain')
				});
				var win_adconnector = put('a', {
						href: _('https://docs.software-univention.de/manual-4.3.html#ad-connector:ad-connector-einrichtung'),
						target: '_blank',
						onmousedown: function(evt) {
						evt.preventDefault();
						_openPageWithTracking(this.href, 'win_adconnector');
					},
					innerHTML: _('Use UCS synchronized with an Active Directory domain')
				});
				var win_admember = put('a', {
						href: _('https://docs.software-univention.de/manual-4.3.html#ad-connector:ad-member-einrichtung'),
						target: '_blank',
						onmousedown: function(evt) {
						evt.preventDefault();
						_openPageWithTracking(this.href, 'win_admember');
					},
					innerHTML: _('Join UCS into an existing Active Directory domain')
				});
				var appcenter = put('a', {
						href: _('https://docs.software-univention.de/quickstart-en-4.3.html#quickstart:updatesinstall'),
						target: '_blank',
						onmousedown: function(evt) {
						evt.preventDefault();
						_openPageWithTracking(this.href, 'appcenter');
					},
					innerHTML: _('Install and use apps from Univention App Center')
				});
				put(ul, 'li', win_domainjoin);
				put(ul, 'li', win_adconnector);
				put(ul, 'li', win_admember);
				put(ul, 'li', appcenter);
				put(ul, 'br');
				put(ul, 'li', manual);

				return ul;
			})()
		}]
	};
});
