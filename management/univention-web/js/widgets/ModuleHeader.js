/*
 * Copyright 2014-2019 Univention GmbH
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
/*global define,document*/

define([
	"dojo/_base/declare",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/i18n!"
], function(declare, ContainerWidget, Text,  _) {

	return declare('umc.widgets.ModuleHeader', [ContainerWidget], {

		baseClass: 'umcModuleHeader',
		isModuleTabSelected: false,
		_title: null,
//		buttons: null,
		_outerContainer: null,

		_setTitleAttr: function(title) {
			this._title.set('content', title);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._left = new ContainerWidget({
				baseClass: 'umcModuleHeaderLeft'
			});
			this._right = new ContainerWidget({
				baseClass: 'umcModuleHeaderRight'
			});
			this._outerContainer = new ContainerWidget({
				baseClass: 'umcModuleHeaderOuterContainer'
			});
			var container = new ContainerWidget({
				baseClass: 'umcModuleHeaderWrapper container'
			});
			this.addChild(this._outerContainer);
			this._outerContainer.addChild(container);
			container.addChild(this._left);
			container.addChild(this._right);

			this._title = new Text({
				content: this.get('title'),
				baseClass: 'umcModuleTitle'
			});
			this._left.addChild(this._title);

//			array.forEach(this.buttons.$order$, lang.hitch(this, function(button) {
//				this._right.addChild(button);
//			}));
		}
	});
});
