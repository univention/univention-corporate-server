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
	"dojo/_base/kernel",
	"dojo/_base/event",
	"dijit/Tooltip",
	"dojo/on",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/widgets/Icon"
], function(declare, kernel, dojoEvent, Tooltip, on, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin) {
	return declare("umc.modules.appcenter.Badge", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppBadge',
		templateString: `
			<div class="umcAppRatingHelp umcAppRatingIcon umcAppRating\${name}" data-dojo-attach-event="onmouseenter:_onMouseEnter">
				<svg data-dojo-type="umc/widgets/Icon" data-dojo-props="iconName: 'star'"></svg>
			</div>
		`,
		_onMouseEnter: function(evt) {
			var node = evt.target;
			Tooltip.show(this.description, node);  // TODO: html encode?
			if (evt) {
				dojoEvent.stop(evt);
			}
			on.once(kernel.body(), 'click', function(evt) {
				Tooltip.hide(node);
				dojoEvent.stop(evt);
			});
		}
	});
});
