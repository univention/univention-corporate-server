/*
 * Copyright 2011 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.StandbyMixin");

dojo.require("dojox.widget.Standby");
dojo.require("dijit._Widget");

dojo.declare("umc.widgets.StandbyMixin", dijit._Widget, {
	// summary:
	//		Mixin class to make a widget "standby-able"

	_standbyWidget: null,

	standbyOpacity: 0.75,

	uninitialize: function() {
		this.inherited(arguments);

		this._standbyWidget.destroy();
	},

	buildRendering: function() {
		this.inherited(arguments);

		// create a standby widget targeted at this module
		this._standbyWidget = new dojox.widget.Standby({
			target: this.domNode,
			duration: 200,
			//zIndex: 99999999,
			opacity: this.standbyOpacity,
			color: '#FFF'
		});
		this.domNode.appendChild(this._standbyWidget.domNode);
		this._standbyWidget.startup();
	},

	_updateContent: function(content) {
		// type check of the content
		if (dojo.isString(content)) {
			// string
			this._standbyWidget.set('text', content);
			this._standbyWidget.set('centerIndicator', 'text');
		}
		else if (dojo.isObject(content) && content.declaredClass && content.domNode) {
			// widget
			this._standbyWidget.set('text', '');
			this._standbyWidget.set('centerIndicator', 'text');

			// hook the given widget to the text node
			dojo.place(content.domNode, this._standbyWidget._textNode);
			content.startup();
		}
		else {
			// set default image
			this._standbyWidget.set('centerIndicator', 'image');
		}
	},

	standby: function(/*Boolean*/ doStandby, /*mixed?*/ content) {
		if (doStandby) {
			// update the content of the standby widget
			this._updateContent(content);

			// show standby widget
			this._standbyWidget.show();
		}
		else {
			// hide standby widget
			this._standbyWidget.hide();
		}
	}
});



