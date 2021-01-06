/*
 * Copyright 2020-2021 Univention GmbH
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
	"dojo/dom-class",
	"dojo/topic",
	"dijit/_Widget",
	"dijit/_TemplatedMixin"
], function(declare, domClass, topic, _Widget, _TemplatedMixin) {
	return declare("umc.modules.appcenter.Tile", [_Widget, _TemplatedMixin], {
		baseClass: 'umcTile',
		templateString: `
			<div data-dojo-attach-event="onclick:_onClick">
				<div
					class="tile__box"
					style="background: \${bgc}"
				>
					<img 
						class="tile__logo"
						src="\${logo}"
						alt="\${name} logo"
					>
				</div>
				<span class="tile__name">\${name}</span>
			</div>
		`,
		_onClick: function() {
			topic.publish('/appcenter/open', this.obj, this.suggested);
		},
		_setVisibleAttr: function(newVal) {
			this._set('visible', newVal);
			domClass.toggle(this.domNode, 'dijitDisplayNone', !newVal);
		}
	});
});








