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
/*global define*/

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/declare",
	"dojo/promise/all",
	"dojo/Deferred",
	"dojo/query",
	"dojo/dom",
	"dojo/dom-class",
	"dojo/dom-attr",
	"dojo/dom-construct",
	"dojo/dom-geometry",
	"dojo/topic",
	"dojo/cookie",
	"dojo/request",
	"dojo/on",
	"dojo/window",
	"login",
	"login/LoginDialog",
	"umc/tools",
	"umc/menu",
	"umc/store",
	"umc/i18n/tools",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/i18n!umc/hooks/univention_demo",
	"xstyle/css!./univention_demo.css"
], function(lang, array, declare, all, Deferred, query, dom, domClass, domAttr, domConstruct, domGeometry, topic, cookie, request, on, win, login, LoginDialog, tools, menu, store, i18nTools, ContainerWidget, Text, Button, _) {
	
	var _fillLoginForm = function () {
		var node = dom.byId("umcLoginPassword");
		if (!node) {
			return;  // not on the login page
		}
		domAttr.set(node, 'value', 'univention');
		node = dom.byId('umcLoginUsername');
		domAttr.set(node, 'value', 'Administrator');
	};

	lang.extend(LoginDialog, {
		_resetFormOld: lang.clone(LoginDialog.prototype._resetForm),
		_resetForm: function() {
			this._resetFormOld();
			_fillLoginForm();
		}
	});
	_fillLoginForm();

	var _InfoBoxWidget = new declare('umc.hooks.univention_demo._InfoBoxWidget', [ContainerWidget], {
		'class': 'umcDemoInfoBox',

		infoText: '',
		referenceNodeSelector: '',
		arrowType: '',

		postMixInProperties: function() {
			this.inherited(arguments);
			this.isLeft = this.arrowType.indexOf('Left') >= 0;
			this.isRight = this.arrowType.indexOf('Right') >= 0;
			this.isBottom = this.arrowType.indexOf('Bottom') >= 0;
			this.isTop = this.arrowType.indexOf('Top') >= 0;
		},

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, this.isLeft ? 'left' : 'right');
			domClass.add(this.domNode, this.isTop ? 'top' : 'bottom');
			this.addChild(new Text({
				'class': lang.replace('umcDemoArrow{arrowType}Icon', this)
			}));
			this.addChild(new Text({
				'class': 'infoText',
				content: this.infoText
			}));
		},

		startup: function() {
			this.updatePosition();
		},

		updatePosition: function() {
			// query reference node
			var result = query(this.referenceNodeSelector);
			if (!result.length) {
				// not found... hide info box
				domClass.add(this.domNode, 'dijitDisplayNone');
				return;
			}

			// adjust position
			domClass.remove(this.domNode, 'dijitDisplayNone');
			var domNode = result[0];
			var referencePos = domGeometry.position(domNode, true);
			var selfSize = domGeometry.position(this.domNode);
			var docSize = domGeometry.position(window.document.body);
			var pos = {
				l: Math.max(0, referencePos.x + referencePos.w / 2 + (this.isRight ? -selfSize.w : 0)),
				t: this.isBottom ? referencePos.y - selfSize.h - 5 : referencePos.y + referencePos.h + 5,
			};
			domGeometry.setMarginBox(this.domNode, pos);

			if (this.isRight) {
				domGeometry.setContentSize(this.domNode, {
					w: Math.min(400, referencePos.x)
				});
			} else {
				domGeometry.setContentSize(this.domNode, {
					w: Math.min(400, docSize.w - pos.l)
				});
			}
		}
	});

	var buildPortalOverlay = function() {
		var resizeHandlers = [];

		var _buildDomElements = function(readme, hideReadme) {
			// build up DOM elements
			var overlayContainer = new ContainerWidget({
				'class': 'umcDemoOverlay'
			});
			var close = function(ev) {
				domClass.add(overlayContainer.domNode, 'dijitDisplayNone');

				if (!hideReadme) {
					// flag via cookie information that the readme has been read
					cookie('UMCDemoReadmeClose', 'true', { path: '/univention' });
				}
			};
			on(overlayContainer.domNode, 'click', close);
			
			var readmeWidget = new Text({
				'class': 'umcDemoReadme',
				content: readme
			});
			overlayContainer.addChild(readmeWidget);

			var closeButton = new Button({
				'class': 'umcDemoReadmeCloseButton',
				iconClass: 'umcCloseIconWhite'
				// onClick: close // not needed since clicking the whole overlay closes the overlay
			});
			domConstruct.place(closeButton.domNode, readmeWidget.domNode, 'first');

			// check whether the README is displayed automatically
			domClass.toggle(overlayContainer.domNode, 'dijitDisplayNone', hideReadme);

			// make sure that the height of the overlay fits the viewport
			var _updateOverlayHeight = function() {
				var docSize = domGeometry.position(window.document.body);
				domGeometry.setMarginBox(overlayContainer.domNode, {
					h: docSize.h
				});
			};
			_updateOverlayHeight();
			resizeHandlers.push(_updateOverlayHeight);

			// align the vertical position of the readme text to be slightly below
			// the first gallery entry
			var _updateReadmePosition = function() {
				var firstGalleryItem = query('.umcGalleryWrapperItem');
				if (!firstGalleryItem.length) {
					return;
				}
				firstGalleryItem = firstGalleryItem[0];
				var pos = domGeometry.position(firstGalleryItem, true);
				domGeometry.setMarginBox(readmeWidget.domNode, {
					t: pos.y + 50
				});
			};
			_updateReadmePosition();
			resizeHandlers.push(_updateReadmePosition);

			return overlayContainer;
		};

		var _buildArrows = function(overlayContainer) {
			var infoBoxes = [];
			infoBoxes.push(new _InfoBoxWidget({
				referenceNodeSelector: '.umcGalleryWrapperItem a[href*="/univention/management"]',
				infoText: _('The UCS web interface for administrating users, computers, etc.'),
				arrowType: 'TopLeft'
			}));
			infoBoxes.push(new _InfoBoxWidget({
				referenceNodeSelector: '.umcGalleryWrapperItem a',
				infoText: _('Dummy entries to apps that could be installed on UCS'),
				arrowType: 'BottomLeft'
			}));
			infoBoxes.push(new _InfoBoxWidget({
				referenceNodeSelector: '.umcMobileMenuToggleButton > div:nth-child(3)',
				infoText: _('This help screen can be displayed again via <i>Help</i> in the user menu'),
				arrowType: 'TopRight'
			}));
			array.forEach(infoBoxes, function(ibox) {
				overlayContainer.addChild(ibox);
			});
			resizeHandlers.push(function() {
				array.forEach(infoBoxes, function(ibox) {
					ibox.updatePosition();
				});
			});
		};

		var resizeDeferred = null;
		var handleWindowResize = function() {
			// handle resize events... wait for 50ms before actually evaluating the new window size
			if (resizeDeferred && !resizeDeferred.isFulfilled()) {
				resizeDeferred.cancel();
			}
			resizeDeferred = tools.defer(function() {
				// call all registered resize handlers
				array.forEach(resizeHandlers, function(ihandler) {
					ihandler();
				});
			}, 50);
			resizeDeferred.otherwise(function() { /* prevent logging of cancel exception */ });
		};

		var addMenuEntry = function(applianceOverlay) {
			menu.addEntry({
				parentMenuId: 'umcMenuHelp',
				label: _('Demo help'),
				priority: 120,
				onClick: function() {
					domClass.remove(applianceOverlay.domNode, 'dijitDisplayNone');
					handleWindowResize();
				}
			});
		};

		// build DOM elements
		var hideReadme = tools.isTrue(cookie('UMCDemoReadmeClose'));
		var overlayContainer = _buildDomElements(_('Welcome to the online demo of Univention Corporate Server (UCS). You are now on the start site of the UCS system. Click on "System and domain settings" to start exploring the possibilities UCS offers.'), hideReadme);
		_buildArrows(overlayContainer);

		// put container into DOM
		overlayContainer.startup();
		domConstruct.place(overlayContainer.domNode, document.body);
		on(window, 'resize', handleWindowResize);
		handleWindowResize();

		// add a menu entry
		addMenuEntry(overlayContainer);
	};

	// only do something on the portal page
	if (window.location.pathname.indexOf('/univention/portal/') === 0) {
		buildPortalOverlay();
	}

	return null;
});
