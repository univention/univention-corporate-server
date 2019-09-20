/*
 * Copyright 2012-2019 Univention GmbH
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
	"dojo/Deferred",
	"dojo/when",
	"dojo/on",
	"dojo/dom-style",
	"dojo/dom-geometry",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget"
], function(declare, lang, array, Deferred, when, on, domStyle, domGeom, Text, Container) {
	return declare("umc.modules.udm.NotificationText", [Container], {
		// summary:
		//		This class extends the normal Container widget in order to encapsulate
		//		some UDM specific notification behavior.

		_text: null,

		_currentAnimation: null, // use to avoid overlapping animations

		buildRendering: function() {
			this.inherited(arguments);

			this._text = new Text({
				labelPosition: 'middle'
			});
			this.own(this._text);
			this.addChild(this._text);
			
			on(this.domNode, 'click', lang.hitch(this, '_hideMessage'));
		},

		postCreate: function() {
			this.inherited(arguments);

			domStyle.set(this.domNode, {
				height: "0",
				margin: "0 -24px",
				position: "relative",
				"-webkit-transition": "height 1s",
				"transition": "height 1s",
				cursor: "pointer"
			});

			domStyle.set(this._text.domNode, {
				overflow: "hidden",
				height: "100%",
				width: "100%"
			});
		},

		showSuccess: function(message) {
			domStyle.set(this.domNode, {
				color: "rgb(60, 118, 61)",
				backgroundColor: "rgb(223, 240, 216)"
			});
			this._showMessage(message);
		},

		_showMessage: function(message) {
			var current_height = domGeom.getContentBox(this.domNode).h;
			var stopDeferred = new Deferred();
			if (current_height > 0) {
				this._hideMessage(stopDeferred);
			} else {
				stopDeferred.resolve();
			}

			when(stopDeferred, lang.hitch(this, function() {
				this.set('message', message);
				domStyle.set(this.domNode, {
					padding: "0.3em 1.6em",
					"margin-bottom": "8px",
					height: "auto"
				});
			}));
		},

		_hideMessage: function(stopDeferred) {
			domStyle.set(this.domNode, {
				padding: "0",
				"margin-bottom": "",
				height: "0"
			});

			if (stopDeferred) {
				setTimeout(stopDeferred.resolve, 1000);
			}
		},

		_setMessageAttr: function(value) {
			if (this._text.domNode) {
				this._text.domNode.textContent = value;
			}
		},

		_getMessageAttr: function() {
			if (this._text.domNode) {
				return this.domNode.textContent;
			} else {
				return null;
			}
		}
	});
});
