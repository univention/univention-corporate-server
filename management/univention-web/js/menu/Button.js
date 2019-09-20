/*
 * Copyright 2017-2019 Univention GmbH
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
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/Deferred",
	"dijit/Tooltip",
	"umc/menu/_Button",
	"umc/tools",
	"umc/i18n!"
], function(declare, Deferred, Tooltip, _Button, tools, _) {

	// require umc/menu here in order to avoid circular dependencies
	var menuDeferred = new Deferred();
	require(["umc/menu"], function(_menu) {
		menuDeferred.resolve(_menu);
	});

	var menuButtonDeferred = new Deferred();

	var MenuButton = declare('umc.menu.Button', [_Button], {
		buildRendering: function() {
			this.inherited(arguments);
			menuDeferred.then(function(menu) {
				menu.createMenu();
			});
			this._tooltip = new Tooltip({
				label: _('Click for menu options'),
				connectId: [ this.domNode ]
			});
			this.own(this._tooltip);
		},

		postCreate: function() {
			this.inherited(arguments);
			menuButtonDeferred.resolve(this);
		}
	});

	MenuButton.menuButtonDeferred = menuButtonDeferred;
	return MenuButton;
});
