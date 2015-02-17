/*
 * Copyright 2015 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/Color",
	"dojo/dom-construct",
	"dojo/mouse",
	"dojo/Deferred",
	"dojox/gfx",
	"dojox/gfx/fx",
	"dijit/form/Button"
], function(declare, lang, Color, domConstruct, mouse, Deferred, gfx, fxg, Button) {
	return declare('umc.app.CategoryButton', Button, {
		color: '#ffffff',
		_surface: null,
		_circle: null,
		_triangle: null,
		_triangleAnimYOffset: 12,
		_animDeferred: null,
		iconClass: '', // to avoid 'dijitNoIcon' to be assigned
		selected: false,

		_createSurface: function() {
			this._surface = gfx.createSurface(this.focusNode, 70, 82);
			domConstruct.place(this._surface.rawNode, this.iconNode, 'after');
			this.color = this.color || '#fff';
		},

		_createCircle: function() {
			var startColor = new Color(this.color);
			var endColor = startColor.toRgba();
			endColor[3] = 0.8; // transparency to 80%
			this._circle = this._surface.createCircle({ cx: 35, cy: 35, r:35 }).setFill({
				type:"linear",
				x1:0, y1:70,
				x2:0, y2:0,
				colors: [
					{ offset: 0, color: startColor },
					{ offset: 1, color: endColor }
				]
			});
		},

		_createTriangle: function() {
			this._triangle = this._surface.createPolyline([
				{x: 28, y: 56},
				{x: 35, y: 70},
				{x: 42, y: 56}
			]).setFill(this.color);
		},

		buildRendering: function() {
			this.inherited(arguments);
			this._createSurface();
			this._createCircle();
			this._createTriangle();
		},

		_moveTriangle: function(ystart, yend) {
			var anim = fxg.animateTransform({
				duration: 200,
				shape: this._triangle,
				transform: [{
					name: 'translate',
					start: [0, ystart],
					end: [0, yend]
				}]
			});

			var deferred = new Deferred();
			this._animDeferred = this._animDeferred.then(lang.hitch(this, function() {
				if (lang.getObject('dy', false, this._triangle.getTransform()) == yend) {
					// no need to replay the animation
					deferred.resolve();
				}
				else {
					// register event handler for deferred
					// and play the animation
					anim.on('End', function() {
						deferred.resolve();
					});
					anim.play();
				}
				return deferred;
			}));
			return deferred;
		},

		_showTriangle: function() {
			this._moveTriangle(0, this._triangleAnimYOffset);
		},

		_hideTriangle: function() {
			this._moveTriangle(this._triangleAnimYOffset, 0);
		},

		postCreate: function() {
			this.inherited(arguments);
			this._animDeferred = new Deferred();
			this._animDeferred.resolve();
			this.on(mouse.enter, lang.hitch(this, function() {
				if (!this.selected) {
					this._showTriangle();
				}
			}));
			this.on(mouse.leave, lang.hitch(this, function() {
				if (!this.selected) {
					this._hideTriangle();
				}
			}));
		},

		_setSelectedAttr: function(val) {
			if (val) {
				this._showTriangle();
			}
			else {
				this._hideTriangle();
			}
			this._set('selected', val);
		},

		_getTriangleVisibleAttr: function() {
			return this._triangle.getTransform().dy == this._triangleAnimYOffset;
		}
	});
});

