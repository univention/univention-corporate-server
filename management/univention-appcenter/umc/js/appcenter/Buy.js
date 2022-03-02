/*
 * Copyright 2020-2022 Univention GmbH
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
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/i18n!umc/modules/appcenter",
	"umc/modules/appcenter/SidebarElement",
	"umc/widgets/Button"
], function(declare, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, _) {
	return declare("umc.modules.appcenter.Buy", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppBuy',

		_header: _("Buy in App Center"),
		_butonLabel: _("Buy now"),

		templateString: `
			<div>
				<div
					data-dojo-type="umc/modules/appcenter/SidebarElement"
					data-dojo-props="
						header: this._header,
						icon: 'shopping-cart'
					"
				>
					<div class="umcAppSidebarButton ucsPrimaryButton"
						data-dojo-type="umc/widgets/Button"
						data-dojo-attach-event="click:_onClick"
						data-dojo-props="
							name: 'shop',
							label: this._butonLabel
						"
					></div>
				</div>
			</div>
		`,
		_onClick: function() {
			this.callback();
		}
	});
});
