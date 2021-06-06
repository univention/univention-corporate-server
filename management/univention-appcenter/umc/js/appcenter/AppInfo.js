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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_Container",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"umc/modules/appcenter/Tile",
	"umc/i18n!umc/modules/appcenter",
	"umc/widgets/Button"
], function(declare, lang, array, domClass, _WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin, Tile, _) {
	return declare("umc.modules.appcenter.AppInfo", [_WidgetBase, _Container, _TemplatedMixin, _WidgetsInTemplateMixin], {
		baseClass: 'umcAppInfo',
		templateString: `
			<div class="appDetailsSidebarElement">
				<div data-dojo-attach-point="containerNode"></div>
				<div class="umcAppInfo__description">\${description}</div>
				<div class="umcAppInfo__buttonWrapper" data-dojo-attach-point="buttonNode">
					<div class="umcAppSidebarButton ucsPrimaryButton"
						data-dojo-type="umc/widgets/Button"
						data-dojo-attach-event="click:_onClick"
						data-dojo-props="
							name: 'installations',
							label: '\${buttonLabel}'
						"
					>
					</div>
				</div>
			</div>
		`,
		buildRendering: function() {
			this.inherited(arguments);
			this.addChild(new Tile({
				bgc: this.bgc,
				logo: this.logo,
				name: this.name
			}));
			if (! this.buttonLabel) {
				domClass.add(this.buttonNode, 'dijitDisplayNone');
			}
		},
		_onClick: function() {
			this.callback();
		}
	});
});
