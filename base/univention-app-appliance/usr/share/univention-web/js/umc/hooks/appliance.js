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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/declare",
	"dojo/promise/all",
	"dojo/Deferred",
	"dojo/query",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/dom-geometry",
	"dojo/topic",
	"dojo/cookie",
	"dojo/request",
	"dojo/on",
	"dojo/window",
	"login",
	"umc/tools",
	"umc/menu",
	"umc/store",
	"umc/i18n/tools",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/i18n!umc/hooks/appliance",
	"xstyle/css!./appliance.css"
], function(lang, array, declare, all, Deferred, query, domClass, domConstruct, domGeometry, topic, cookie, request, on, win, login, tools, menu, store, i18nTools, ContainerWidget, Text, Button, _) {
	var _InfoBoxWidget = new declare('umc.hooks.appliance._InfoBoxWidget', [ContainerWidget], {
		'class': 'umcApplianceInfoBox',

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
				'class': lang.replace('umcApplianceArrow{arrowType}Icon', this)
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

		var _buildDomElements = function(applianceName, readme, hideReadme) {
			// build up DOM elements
			var overlayContainer = new ContainerWidget({
				'class': 'umcApplianceOverlay'
			});
			var readmeWidget = new Text({
				'class': 'umcApplianceReadme',
				content: readme
			});
			overlayContainer.addChild(readmeWidget);

			var h1Node = domConstruct.toDom('<h1>' + _('%s Appliance', applianceName) + '</h1>');
			domConstruct.place(h1Node, readmeWidget.domNode, 'first');

			var closeButton = new Button({
				'class': 'umcApplianceReadmeCloseButton',
				iconClass: 'umcCloseIconWhite',
				onClick: function() {
					domClass.add(overlayContainer.domNode, 'dijitDisplayNone');

					if (!hideReadme) {
						// flag via cookie information that the readme has been read
						cookie('UMCApplianceReadmeClose', 'true', { path: '/univention' });
					}
				}
			});
			domConstruct.place(closeButton.domNode, readmeWidget.domNode, 'first');

			// check whether the README is displayed automatically
			domClass.toggle(overlayContainer.domNode, 'dijitDisplayNone', hideReadme);

			// make sure that the height of the overlay fits the viewport
			var _updateOverlayHeight = function() {
				var docSize = domGeometry.position(window.document.body);
				domGeometry.setMarginBox(overlayContainer.domNode, {
					// add a slight offset to have enough space for the hint at the bottom
					h: docSize.h + 75
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
					t: pos.y + 10
				});
			};
			_updateReadmePosition();
			resizeHandlers.push(_updateReadmePosition);

			return overlayContainer;
		};

		var _buildArrows = function(overlayContainer, applianceName) {
			var infoBoxes = [];
			infoBoxes.push(new _InfoBoxWidget({
				referenceNodeSelector: '.umcGalleryWrapperItem a[href*="/univention/management"]',
				infoText: _('Univention Management Console (UMC) for administrating users, computers, etc.'),
				arrowType: 'TopLeft'
			}));
			infoBoxes.push(new _InfoBoxWidget({
				referenceNodeSelector: '.umcGalleryWrapperItem a',
				infoText: _('%s web interface', applianceName),
				arrowType: 'BottomLeft'
			}));
			infoBoxes.push(new _InfoBoxWidget({
				referenceNodeSelector: '.umcMobileMenuToggleButton > div:nth-child(3)',
				infoText: _('Display this information again via <i>Help</i> in the user menu'),
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
				label: _('First steps help'),
				priority: 120,
				onClick: function() {
					domClass.remove(applianceOverlay.domNode, 'dijitDisplayNone');
					handleWindowResize();
				}
			});
		};

		// try to fetch German and English README files
		var readmePath = require.toUrl('umc/hooks/appliance_readme_{0}');
		var requests = {
			de: request(lang.replace(readmePath, ['de'])).then(null, function(err) { return null; }),
			en: request(lang.replace(readmePath, ['en'])).then(null, function(err) { return null; }),
			data: request(require.toUrl('umc/hooks/appliance.json'), {
				handleAs: 'json'
			}).then(null, function(err) { return null; })
		};

		all(requests).then(function(result) {
			var language = i18nTools.defaultLang().split('-')[0];
			var readme = result[language] || result.en || null;
			if (!readme) {
				// no README file provided
				return;
			}

			// build DOM elements
			var applianceName = lang.getObject('data.appliance_name', false, result);
			var hideReadme = tools.isTrue(lang.getObject('data.close_first_steps', false, result));
			var overlayContainer = _buildDomElements(applianceName, readme, hideReadme);
			_buildArrows(overlayContainer, applianceName);

			// put container into DOM
			overlayContainer.startup();
			domConstruct.place(overlayContainer.domNode, document.body);
			on(window, 'resize', handleWindowResize);
			handleWindowResize();

			// add a menu entry
			addMenuEntry(overlayContainer);
		});
	};

	var _saveReadmeClose = function() {
		if (cookie('UMCApplianceReadmeClose') == 'true') {
			var ucrStore = store('key', 'ucr');
			ucrStore.put({
				key: 'umc/web/appliance/close_first_steps',
				value: 'yes'
			});
		}
	};

	// only do something on the portal page
	if (window.location.pathname.indexOf('/univention/portal/') === 0) {
		buildPortalOverlay();
	}
	login.onLogin(_saveReadmeClose);

	return null;
});
