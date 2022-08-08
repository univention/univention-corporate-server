/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2019-2022 Univention GmbH
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
	"dojo/dom-class",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin"
], function(declare, lang, domClass, _WidgetBase, _TemplatedMixin) {
	return declare("umc.modules.setup.ChooseRoleBox", [_WidgetBase, _TemplatedMixin], {
		// summary:
		//		Simple widget that displays a link.

		templateString: '<div><div class="umcChooseRoleBox__headline">${headline}<div class="umcChooseRoleBox__tag">${tag}</div></div><div class="umcChooseRoleBox__content">${content}</div></div>',

		// headline: String
		//		String which contains the role text.
		headline: '',

		// tag: String
		//		Small hints regarding this role.
		tag: '',

		// content: String
		//		String which contains the description text.
		content: '',

		// the widget's class name as CSS class
		baseClass: 'umcChooseRoleBox',

		// value: bool
		//		Active?
		value: false,

		// callback: function
		//		What happens if a user actually chooses the role by clicking the box?
		callback: null,

		postCreate: function() {
			this.inherited(arguments);

			this.on('click', lang.hitch(this, function() {
				this.set('value', !this.get('value'));
				if (this.callback) {
					this.callback(this.name);
				};
			}));
		},

		_setValueAttr: function(newVal) {
			domClass.toggle(this.domNode, 'umcChooseRoleBox--selected', newVal);
			this._set('value', newVal);
		}
	});
});
