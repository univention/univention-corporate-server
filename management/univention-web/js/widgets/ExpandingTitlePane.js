/*
 * Copyright 2011-2019 Univention GmbH
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
	"dojo/_base/kernel",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page"
], function(declare, lang, array, kernel, ContainerWidget, Page) {
	return declare("umc.widgets.ExpandingTitlePane", ContainerWidget, {
		// summary:
		//		Obsolete widget which adds itself to the parent and removes its domNode

		style: 'display: none;',
		parentWidget: null,

		constructor: function() {
			this.inherited(arguments);
			kernel.deprecated('umc.widgets.ExpandingTitlePane', 'do not use it anymore!');
			this._widgets = [];
		},

		getParentWidget: function() {
			// usually parentNode.parentNode should be a Page object
			var widget = this.getParent().getParent();
			if (!widget || !widget.isInstanceOf(Page)) {
				// no Page object -> fallback to the next parent widget
				widget = this.getParent();
			}
			return widget;
		},

		__addChild: function(child) {
			if (this.parentWidget && this.parentWidget.addChild) {
				this.parentWidget.addChild(child);
			}
		},

		addChild: function(child) {
			if (!this._started) {
				this._widgets.push(child);
			} else {
				this.__addChild(child);
			}
		},

		getChildren: function() {
			if (this.parentWidget && this.parentWidget.getChildren) {
				return this.parentWidget.getChildren();
			}
			return this.inherited(arguments);
		},

		startup: function() {
			this.inherited(arguments);

			if (this.parentWidget) {
				return;
			}
			// get the parent node and remove ourself from the DOM
			this.parentWidget = this.getParentWidget();
			this.domNode.parentNode.removeChild(this.domNode);
			this.domNode = null;
			this.parentWidget.own(this);

			// add all buffered child widgets to the DOM
			array.forEach(this._widgets, lang.hitch(this, '__addChild'));
			this._widgets = [];
		}
	});
});
