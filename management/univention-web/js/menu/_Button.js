/*
 * Copyright 2017-2019 Univention GmbH
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
/*global define,dojo*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/on",
	"dojo/Deferred",
	"dojo/mouse",
	"dojo/touch",
	"dojox/gesture/tap",
	"dojo/has",
	"dojo/dom-class",
	"umc/tools",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dojo/sniff" // has("ie"), has("ff")
], function(declare, lang, on, Deferred, mouse, touch, tap, has, domClass, tools, _WidgetBase, _TemplatedMixin) {

	// require umc/menu here in order to avoid circular dependencies
	var menuDeferred = new Deferred();
	require(["umc/menu"], function(_menu) {
		menuDeferred.resolve(_menu);
	});

	return declare('umc.menu._Button', [_WidgetBase, _TemplatedMixin], {
		mobileToggleMouseLeave: null,

		templateString: '' +
			'<div class="umcMobileMenuToggleButton">' +
				'<div></div>' +
				'<div></div>' +
				'<div></div>' +
				'<div class="umcMobileMenuToggleButtonTouchStyle"></div>' +
			'</div>',

		buildRendering: function() {
			this.inherited(arguments);

			// add listeners
			if (has('touch')) {
				this.on(touch.press, function() {
					domClass.add(this, 'umcMobileMenuToggleButtonTouched');
				});
				this.on([touch.leave, touch.release], function() {
					tools.defer(lang.hitch(this, function() {
						domClass.remove(this, 'umcMobileMenuToggleButtonTouched');
					}), 300);
				});
			} else {
				this.on(mouse.enter, function() {
					domClass.add(this, 'umcMobileMenuToggleButtonHover');
				});
				this.mobileToggleMouseLeave = on.pausable(this.domNode, mouse.leave, function() {
					domClass.remove(this, 'umcMobileMenuToggleButtonHover');
				});
			}
			this.on(tap, lang.hitch(this, 'toggleButtonClicked'));
		},

		toggleButtonClicked: function() {
			if (this.mobileToggleMouseLeave) {
				this.mobileToggleMouseLeave.pause();
			}
			tools.defer(lang.hitch(this, function() {
				domClass.remove(this.domNode, 'umcMobileMenuToggleButtonHover');
			}, 510)).then(lang.hitch(this, function() {
				if (this.mobileToggleMouseLeave) {
					this.mobileToggleMouseLeave.resume();
				}
			}));
			if (domClass.contains(dojo.body(), 'mobileMenuActive')) {
				menuDeferred.then(function(menu) {
					menu.close();
				});
			} else {
				menuDeferred.then(function(menu) {
					menu.open();
				});
			}
		}
	});
});
