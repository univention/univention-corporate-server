/*
 * Copyright 2011-2017 Univention GmbH
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
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/_base/fx",
	"dojo/topic",
	"dojo/aspect",
	"dojo/dom-class",
	"dojo/dom-style",
	"dojo/dom-geometry",
	"dojo/window",
	"dojo/on",
	"dojo/fx/easing",
	"dijit/layout/StackContainer",
	"dojox/html/entities",
	"umc/tools",
	"umc/render",
	"umc/widgets/_ModuleMixin",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ModuleHeader",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Button",
	"put-selector/put",
	"umc/i18n!"
], function(declare, lang, array, baseWindow, baseFx, topic, aspect, domClass, domStyle, domGeom, win, on, fxEasing, StackContainer, entities, tools, render, _ModuleMixin, ContainerWidget, ModuleHeader, StandbyMixin, Button, put, _) {
	return declare("umc.widgets.Module", [ContainerWidget, _ModuleMixin, StandbyMixin], {
		// summary:
		//		Basis class for module classes.

		_top: null,
		_bottom: null,
		__container: null,

		// initial title set for the module
		defaultTitle: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.defaultTitle = this.title;

			this.__container = new declare([StackContainer, StandbyMixin])({
				baseClass: StackContainer.prototype.baseClass + ' umcModuleContent',
				doLayout: false
			});
			this.__container.watch('selectedChildWidget', lang.hitch(this, function(name, oldV, newV) {
				this.set(name, newV);
			}));

			this.__container.watch('selectedChildWidget', lang.hitch(this, '__refreshButtonVisibility'));
			this.own(aspect.after(this.__container, 'addChild', lang.hitch(this, function(child) {
				this._addHeaderButtonsToChild(child);
				child.own(child.watch('headerButtons', lang.hitch(this, function() {
					this._addHeaderButtonsToChild(child);
				})));
			}), true));
		},

		resetTitle: function() {
			this.set('title', this.defaultTitle);
		},

		_setTitleAttr: function(title) {
			// dont set html attribute title
			// (looks weird)
			this._set('title', title);
			if (this._top) {
				this._top.set('title', title);
			}
		},

		_setTitleDetailAttr: function(detail) {
			var title = this.defaultTitle;
			if (detail) {
				title += ': ' + entities.encode(detail);
			}
			this.set('title', title);
			this._set('titleDetail', detail);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._bottom = new ContainerWidget({
				baseClass: 'umcModuleWrapper',
				'class': 'container'
			});
			this._bottom.addChild(this.__container);

			this._top = new ModuleHeader({
				//buttons: render.buttons(this.headerButtons, this),
				title: this.get('title')
			});

			var scrollToTopFloatingButton = new ContainerWidget({
				'class': 'scrollToTopFloatingButton'
			});
			var ink = put(scrollToTopFloatingButton.domNode, 'div.icon + div.ink');
			scrollToTopFloatingButton.on('click', function(e) {
				// show ink effect
				var floatingButtonDiameter = domGeom.position(scrollToTopFloatingButton.domNode).w;
				var floatingButtonLeft = scrollToTopFloatingButton.domNode.offsetLeft;
				var floatingButtonTop = scrollToTopFloatingButton.domNode.offsetTop;
				var innerClickX = e.clientX - floatingButtonLeft;
				var innerClickY = e.clientY - floatingButtonTop;
				var inkDiameter = Math.max(
					(floatingButtonDiameter - innerClickX),
					innerClickX,
					(floatingButtonDiameter - innerClickY),
					innerClickY
				) * 2;
				var inkRadius = inkDiameter / 2;
				var x = innerClickX - inkRadius;
				var y = innerClickY - inkRadius;
				domStyle.set(ink, {
					'transition': 'none',
					'opacity': '',
					'transform': '',
					'left': x + 'px',
					'top': y + 'px',
					'width': inkDiameter + 'px',
					'height': inkDiameter + 'px'
				});
				setTimeout(function() {
					domStyle.set(ink, {
						'transition': '',
						'opacity': '0',
						'transform': 'scale(1)'
					});
				}, 20);

				// scroll to top of window
				new baseFx.Animation({
					duration: 300,
					easing: fxEasing.cubicOut,
					curve: [dojo.docScroll().y, 0],
					onAnimate: function(val) {
						window.scrollTo(0, val);
					}
				}).play();
			});

			var scrollToTopFloatingButtonSpacer = new ContainerWidget({
				'class': 'scrollToTopFloatingButtonSpacer'
			});

			ContainerWidget.prototype.addChild.apply(this, [this._top]);
			ContainerWidget.prototype.addChild.apply(this, [this._bottom]);
			ContainerWidget.prototype.addChild.apply(this, [scrollToTopFloatingButton]);
			ContainerWidget.prototype.addChild.apply(this, [scrollToTopFloatingButtonSpacer]);

			// redirect childrens to stack container
			this.containerNode = this.__container.containerNode;

			this.own(on(baseWindow.doc, 'scroll', lang.hitch(this, function() {
				if (!this.selected) {
					return;
				}

				// update scrollToTop Button visibility
				var showScrollToTopButton = dojo.docScroll().y >= 300;
				domClass.toggle(scrollToTopFloatingButton.domNode, 'shown', showScrollToTopButton);
				domClass.toggle(scrollToTopFloatingButtonSpacer.domNode, 'shown', showScrollToTopButton);
			})));
		},

		selectChild: function(child, animate) {
			return this.__container.selectChild(child, animate);
		},

		onClose: function() {
			if (this.__container && this.__container.onClose) {
				/*return*/ this.__container.onClose();
			}
			return true;
		},

		addChild: function(child, idx) {
			return this.__container.addChild(child, idx);
		},

		removeChild: function(child) {
			return this.__container.removeChild(child);
		},

		_addHeaderButtonsToChild: function(child) {
			// some default buttons (e.g. close)
			var headerButtons = [/*{
				name: 'help',
				label: _('Help'),
				iconClass: 'umcHelpIconWhite',
				'class': 'umcHelpButton',
				callback: lang.hitch(this, function() {
					topic.publish('/umc/tabs/help', this);
				})
			}*/];
			if (this.closable) {
				headerButtons.push({
					name: 'close',
					label: _('Close'),
					callback: lang.hitch(this, 'closeModule')
				});
			}

			if (child.headerButtons) {
				headerButtons = child.headerButtons.concat(headerButtons);
			}

			if (child.$headerButtons$) {
				this._top._right.removeChild(child.$headerButtons$);
				child.$headerButtons$.destroyRecursive();
				delete child.$headerButtons$;
			}

			// make sure no icons are shown in the module header
			array.forEach(headerButtons, function(btn) {
				delete btn.iconClass;
			});

			child._headerButtons = null;
			if (headerButtons && headerButtons.length) {
				var container = new ContainerWidget({
					style: 'display: inline-block; margin: 0; padding: 0;'
				});
				child.own(container);

				child._headerButtons = render.buttons(headerButtons.reverse(), container);
				array.forEach(child._headerButtons.$order$.reverse(), function(btn) {
					container.addChild(child._headerButtons[btn.name]); // important! allow overwriting of button names (e.g close)
					btn.on('mouseEnter', function() {
						domClass.add(btn.domNode, 'dijitButtonHover');
						var labelBox = domGeom.getMarginBox(btn.containerNode);
						var buttonBox = domGeom.position(btn.focusNode);
						var halfWidth = (labelBox.w - buttonBox.w) / 2;
						var distanceToBrowserWindow = win.getBox().w - buttonBox.x;
						var offset = Math.max(halfWidth, labelBox.w - distanceToBrowserWindow + 5);
						domGeom.setMarginBox(btn.containerNode, {l: -offset});
					});
				});

				this._top._right.addChild(container, 0);
				child.$headerButtons$ = container;
				container.$child$ = child;
			}
			if (this._started) {
				this.__refreshButtonVisibility();
			}
		},

		__refreshButtonVisibility: function() {
			var child = this.__container.get('selectedChildWidget');
			array.forEach(this._top._right.getChildren(), lang.hitch(this, function(ctn) {
				if (ctn.$child$) {
					domClass.toggle(ctn.domNode, 'dijitDisplayNone', ctn.$child$ !== child);
				}
			}));
		},

		layout: function() {
			this.__container.layout();
		},

		closeModule: function() {
			if (this.closable) {
				topic.publish('/umc/tabs/close', this);
			}
		},

		startup: function() {
			this.__container.startup();
			if (this.__container.selectedChildWidget) {
				this.set('selectedChildWidget', this.__container.selectedChildWidget);
				this.__refreshButtonVisibility();
			}
			this.inherited(arguments);
		}
	});
});
