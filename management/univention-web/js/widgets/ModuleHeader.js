/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2014-2022 Univention GmbH
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
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/tools",
	"umc/i18n!"
], function(declare, domClass, ContainerWidget, Text, tools, _) {
	return declare('umc.widgets.ModuleHeader', [ContainerWidget], {
		baseClass: 'umcModuleHeader',

		isModuleTabSelected: false,

		_outerContainer: null, // ContainerWidget
		_right: null, // ContainerWidget
		_left: null, // ContainerWidget

		_title: null, // Text
		title: '',
		_setTitleAttr: function(title) {
			this._title.set('content', title);
			this._set('title', title);
		},

		_subTitle: null, // Text
		subTitle: '',
		_setSubTitleAttr: function(subTitle) {
			tools.toggleVisibility(this._subTitle, !!subTitle);
			this._subTitle.set('content', subTitle);
			domClass.toggle(this.domNode, this.baseClass + '--withSubTitle', !!subTitle);
			this._set('subTitle', subTitle);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._outerContainer = new ContainerWidget({
				baseClass: 'umcModuleHeaderOuterContainer'
			});
			var container = new ContainerWidget({
				baseClass: 'umcModuleHeaderWrapper container'
			});
			this._left = new ContainerWidget({
				baseClass: 'umcModuleHeaderLeft'
			});
			this._right = new ContainerWidget({
				baseClass: 'umcModuleHeaderRight'
			});
			this._title = new Text({
				content: this.get('title'),
				baseClass: 'umcModuleTitle'
			});
			this._subTitle = new Text({
				content: this.get('subTitle'),
				baseClass: 'umcModuleSubTitle',
				'class': 'dijitDisplayNone'
			});

			this.addChild(this._outerContainer);
			this._outerContainer.addChild(container);
			container.addChild(this._left);
			container.addChild(this._right);
			this._left.addChild(this._title);
			this._left.addChild(this._subTitle);
		}
	});
});
