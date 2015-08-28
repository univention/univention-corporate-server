/*
 * Copyright 2012-2015 Univention GmbH
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
/*global define require console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/Deferred",
	"dojo/when",
	"dojo/dom-style",
	"dojo/_base/fx",
	"dojo/fx",
	"dojo/fx/easing",
	"umc/widgets/Text",
	"umc/widgets/ContainerWidget"
], function(declare, lang, array, Deferred, when, domStyle, baseFx, coreFx, easing, Text, Container) {
	return declare("umc.modules.udm.NotificationText", [Container], {
		// summary:
		//		This class extends the normal Container widget in order to encapsulate
		//		some UDM specific notification behaviour.

		_text: null,

		_currentAnimation: null, // use to avoid overlapping animations

		buildRendering: function() {
			this.inherited(arguments);

			this._text = new Text({
				labelPosition: 'middle'
			});
			this.own(this._text);
			this.addChild(this._text);
		},

		postCreate: function() {
			this.inherited(arguments);

			domStyle.set(this.domNode, {
				height: "0",
				margin: "10px -500px 0 -500px",
				padding: "3px 500px",
				position: "relative"
			});

			domStyle.set(this._text.domNode, {
				fontSize: "14px",
				overflow: "hidden",
				padding: "0 5px",
				height: "100%",
				width: "100%"
			});
		},

		showSuccess: function(message) {
			domStyle.set(this.domNode, {
				backgroundColor: "#dff0d8",
				color: "#3c763d"
			});
			this._showMessage(message);
		},

		_showMessage: function(message) {
			var stopDeferred = new Deferred();
			if (this.get('message')) {
				this._stopCurrentAnimation(stopDeferred);
			} else {
				stopDeferred.resolve();
			}

			when(stopDeferred, lang.hitch(this, function() {
				this.set('message', message);
				this._currentAnimation = baseFx.animateProperty({
					node: this.domNode,
					duration: 350,
					easing: easing.quadIn,
					properties: {
						height: { start: 0, end: 24 },
						paddingTop: { start: 0, end: 3 }
					}
				});
				this._currentAnimation.play();
			}));
		},

		_stopCurrentAnimation: function(stopDeferred) {
			if (this._currentAnimation) {
				this._currentAnimation.stop();
				this._currentAnimation = null;
			}

			baseFx.animateProperty({
				node: this.domNode,
				duration: 350,
				easing: easing.quadOut,
				properties: {
					height: { start: 24, end: 0 },
					paddingTop: { start: 3, end: 0}
				},
				onEnd: lang.hitch(this, function() {
					this.set('message', null);
					stopDeferred.resolve();
				})
			}).play();
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
