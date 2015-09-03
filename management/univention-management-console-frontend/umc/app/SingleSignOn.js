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
/*global define console window setTimeout */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojox/html/styles",
	"umc/tools",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Button",
	"umc/widgets/Text",
	"umc/widgets/ComboBox",
	"umc/widgets/StandbyMixin",
	"umc/i18n!",
	"dojo/domReady!",
	"dojo/NodeList-dom"
], function(declare, lang, array, styles, tools, ContainerWidget, Button, Text, ComboBox, StandbyMixin, _) {
	return declare("umc.app.SingleSignOn", [ContainerWidget], {
		_languageMenu: null,
		_languageButton: null,

		style: 'float: left; padding-top: 2px;',

		buildRendering: function() {
			this.inherited(arguments);
			styles.insertCssRule('#umcSingleSignOn .dijitButtonNode', 'border: 0 none; box-shadow: none; background: none; filter: none;');
			styles.insertCssRule('#umcSingleSignOn .dijitButtonNode .dijitIcon', 'background-position: -140px -20px;');
			this.addChild(new Button({
				label: _('Single sign on'),
				iconClass: 'umcPlayIcon',
				description: _('<b>Warning:</b> Make sure hostnames of this UCS domain %s can be resolved by your browser.', '%s'),
				callback: function() {
					window.location.pathname = '/umcp/saml/';
				}
			}));
		}
	});
});
