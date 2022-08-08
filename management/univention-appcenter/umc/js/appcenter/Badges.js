/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-construct",
	"dojox/html/entities",
	"dijit/_WidgetBase",
	"dijit/_Container",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/modules/appcenter/Badge",
	"umc/i18n!umc/modules/appcenter",
	"umc/modules/appcenter/SidebarElement"
], function(declare, lang, array, domConstruct, entities, _WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin, Badge, _) {
	return declare("umc.modules.appcenter.Badges", [_WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppBadges',
		buttonLabel: _("Manage installations"),

		_header: _('App Center Badges'),

		templateString: `
			<div>
				<div
					data-dojo-type="umc/modules/appcenter/SidebarElement"
					data-dojo-props="
						header: this._header,
						icon: 'bookmark'
					"
				>
					<div data-dojo-attach-point="containerNode"></div>
				</div>
			</div>
		`,

		addBadge: function(name, description) {
			var badge = new Badge({name: name, description: description});
			this.addChild(badge);
		}
	});
});
