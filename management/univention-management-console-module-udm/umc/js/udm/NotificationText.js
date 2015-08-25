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
	"dojo/dom-style",
	"dojo/_base/fx",
	"dojo/fx",
	"dojo/fx/easing",
	"umc/widgets/Text"
], function(declare, lang, array, domStyle, baseFx, coreFx, easing, Text) {
	return declare("umc.modules.udm.NotificationText", [ Text ], {
		// summary:
		//		This class extends the normal Text widget in order to encapsulate
		//		some UDM specific behaviour.

		_siblingNode: null,

		_animations: null, // use to avoid overlapping animations

		labelPosition: 'middle',

		postCreate: function() {
			this.inherited(arguments);
			this._animations = [];
			this.set('visible', false);
			domStyle.set(this.domNode, {
				borderSizing: 'border-box',
				height: "0px",
				width: "100%",
			});
			this._siblingNode.appendChild(this.domNode);
		},

		_showMessage: function(message) {
			this.set('content', message);
			this.set('visible', true);
			
			// stop all animations
			if (this._animations.length) {
				array.forEach(this._animations, function(anim) {
					anim.stop();
				});
				this._animations = [];
			}

			this._animations.push(baseFx.animateProperty({
				node: this.domNode,
				duration: 1000,
				easing: easing.quadOut,
				properties: {
					padding: { end: 5, units: 'px' },
					opacity: { start: 0, end: 1 },
					height: { start: 0, end: 30}
				}
			}));
			this._animations.push(baseFx.animateProperty({
				node: this.domNode,
				delay: 1500,
				duration: 1000,
				easing: easing.quadIn,
				properties: {
					padding: { end: 0, units: 'px' },
					opacity: { start: 1, end: 0 },
					height: { start: 30, end: 0}
				},
				onEnd: lang.hitch(this, function() {
					this.set('content', '');
				})
			}));
			coreFx.chain(this._animations).play();
		},

		showSuccess: function(message) {
			domStyle.set(this.domNode, {
				backgroundColor: '#dff0d8',
				color: '#3c763d',
				
			});
			this._showMessage(message);
		}
	});
});

