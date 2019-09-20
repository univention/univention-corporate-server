/*
 * Copyright 2016-2019 Univention GmbH
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
/*global define, window, location*/

/**
 * @module portal/PortalGallery
 * @extends module:umc/widgets/AppGallery
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/aspect",
	"dojo/query",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/dom-geometry",
	"dojo/dom-style",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dojo/dnd/Source",
	"put-selector/put",
	"umc/tools",
	"umc/widgets/AppGallery",
	"./tools"
], function(declare, lang, array, on, aspect, query, domClass, domConstruct, domGeometry, domStyle, Memory, Observable, Source, put, tools, AppGallery, portalTools) {
	var _regIPv6Brackets = /^\[.*\]$/;

	var find = function(list, testFunc) {
		var results = array.filter(list, testFunc);
		return results.length ? results[0] : null;
	};

	var getHost = function(/*Array*/ ips, /*string*/ fqdn) {
		var host = window.location.host;

		if (tools.isIPv6Address(host)) {
			var ipv6 = find(ips, tools.isIPv6Address);
			if (ipv6 && !_regIPv6Brackets.test(ipv6)) {
					return '[' + ipv6 + ']';
			}
			if (ipv6) {
				return ipv6;
			}
			// use IPv4 as fallback
			return find(ips, tools.isIPv4Address);
		}
		if (tools.isIPv4Address(host)) {
			return find(ips, tools.isIPv4Address);
		}
		return fqdn;
	};

	return declare("PortalGallery", [ AppGallery ], /** @lends module:portal/PortalGallery# */ {
		/**
		 * See {@link module:umc/widgets/GalleryPane#doSetGalleryItemContextMenuHandlers}
		 * @type {Boolean}
		 * @default false
		 */
		doSetGalleryItemContextMenuHandlers: false,

		iconClassPrefix: 'umcPortal',

		domainName: null,

		/**
		 * Defines whether portal entries are opened in the same window or in a new window/tab by default.
		 * (The possible values are defined by the python univention.admin.syntax.PortalDefaultLinkTarget syntax class.)
		 * @type {?String}
         */
		defaultLinkTarget: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.baseClass += ' umcPortalGallery';
		},

		buildRendering: function() {
			domClass.add(this.domNode, this.baseClass);

			switch (this.renderMode) {
				case portalTools.RenderMode.NORMAL:
					this.inherited(arguments);
					break;
				case portalTools.RenderMode.EDIT:
					this.inherited(arguments);
					this._registerEventHandlersForEditMode();
					break;
				case portalTools.RenderMode.DND:
					// no this.inherited(arguments); is intentional
					this._createDndSource();
					this._createDndPlaceholder();
					break;
			}
		},

		_registerEventHandlersForEditMode: function() {
			this.own(on(this.contentNode, '.editEntryTile:click', lang.hitch(this, function(evt) {
				evt.stopImmediatePropagation();
				var entry = this.row(evt).data;
				this.onEditEntry(entry);
			})));
			this.own(on(this.contentNode, '.addEntryTile:click', lang.hitch(this, function(evt) {
				evt.stopImmediatePropagation();
				this.onAddEntry();
			})));
			this.own(on(this.contentNode, '.notInPortalJSONTile:click', lang.hitch(this, function(evt) {
				evt.stopImmediatePropagation();
				var entry = this.row(evt).data;
				this.onEntryNotInPortalJSON(entry);
			})));
		},

		_createDndSource: function() {
			this.contentNode = this.domNode; // the resizing methods need this.contentNode to be set
			put(this.domNode, '.dojoDndSource_PortalEntries');
			this.dndSource = new Source(this.domNode, {
				type: ['PortalEntries'],
				accept: ['PortalEntry'],
				horizontal: true,
				copyState: function() {
					return false; // do not allow copying
				},
				creator: lang.hitch(this, function(item, hint) {
					var node = this.renderRow(item);

					if (hint === 'avatar') {
						node = put('div.umcAppGallery', node); // wrap the tile in div a with class umcAppGallery for correct styling
						this._resizeItemNamesOfAvatarTile(node);
						return { node: node };
					}

					return {
						node: put('div', node), // wrap the tile so that the margin is part of the node and there is is no gap between the tiles
						data: item,
						type: ['PortalEntry']
					};
				})
			});
		},

		_createDndPlaceholder: function() {
			this.dndPlaceholder = domConstruct.toDom('' +
				'<div class="dndPlaceholder dojoDndItem">' +
					'<div class="umcGalleryWrapperItem addEntryTile">' +
						'<div class="cornerPiece boxShadow bl">' +
							'<div class="hoverBackground"></div>' +
						'</div>' +
						'<div class="cornerPiece boxShadow tr">' +
							'<div class="hoverBackground"></div>' +
						'</div>' +
						'<div class="cornerPiece boxShadowCover bl"></div>' +
					'</div>' +
				'</div>'
			);
			this.dndPlaceholderHideout = put(this.domNode, 'div.dndPlaceholderHideout');
			put(this.dndPlaceholderHideout, this.dndPlaceholder);

			this._registerEventHandlersForDndPlaceholder();
		},

		_registerEventHandlersForDndPlaceholder: function() {
			//// move the dndPlaceholder around
			this.own(aspect.after(this.dndSource, '_addItemClass', lang.hitch(this, function(target, cssClass) {
				if (this.dndSource.isDragging) {
					if (target === this.dndPlaceholder) {
						return;
					}

					// if the placeholder tile is not placed yet, ...
					if (this.dndPlaceholderHideout.firstChild === this.dndPlaceholder) {
						// and we come from outside the dndSource,
						// place the placeholder in place of hovered tile
						if (!this.dndSource.current && this.dndSource.anchor /* check for anchor to see if we are in the same category as the dragged tile */) {
							var putCombinator = query(lang.replace('#{0} ~ #{1}', [this.dndSource.anchor.id, target.id]), this.dndSource.parent).length ? '+' : '-';
							put(target, putCombinator, this.dndPlaceholder);
						} else {
							// this case is when the drag event is started.
							// Put the placeholder in the place of the dragged tile
							put(target, '-', this.dndPlaceholder);
						}
						return;
					}

					// if we hover over a different tile while dragging and while the placeholder tile is placed
					// we move the placeholder tile to the hovered tile
					if (cssClass === 'Over') {
						// if we hover a tile to the right of the placeholder we want to place the placeholder to the right of the hovered tile
						// and vice versa
						var putCombinator = query(lang.replace('#{0} ~ .dndPlaceholder', [target.id]), this.dndSource.parent).length ? '-' : '+';
						put(target, putCombinator, this.dndPlaceholder);
					}
				}
			}), true));
			// when we are dragging a tile but are not hovering over a different tile
			// then we want to add the dndPlaceholder at the end of the gallery
			this.own(aspect.after(this.dndSource, 'onMouseMove', lang.hitch(this, function() {
				if (!this.dndSource.isDragging) {
					return;
				}
				if (!this.dndSource.current && this.dndSource.parent.lastChild !== this.dndPlaceholder) {
					put(this.dndSource.parent, this.dndPlaceholder);
				}
			})));

			//// put the dndPlaceholder back into dndPlaceholderHideout
			this.own(aspect.before(this.dndSource, 'onDropInternal', lang.hitch(this, function() {
				if (!this.dndSource.current && this.dndSource.parent.lastChild === this.dndPlaceholder) {
					this.dndSource.current = this.dndPlaceholder.previousSibling;
				}
			})));
			this.own(aspect.after(this.dndSource, 'onDndCancel', lang.hitch(this, function() {
				put(this.dndPlaceholderHideout, this.dndPlaceholder);
			})));
			this.own(aspect.after(this.dndSource, 'onDraggingOut', lang.hitch(this, function() {
				put(this.dndPlaceholderHideout, this.dndPlaceholder);
			})));
		},

		startup: function() {
			// Initial rendering of the entries.
			// Since we need the PortalGallery to be in the dom for sizing
			// purposes we set the store attribute here and not earlier.
			switch (this.renderMode) {
				case portalTools.RenderMode.NORMAL:
				case portalTools.RenderMode.EDIT:
					var store = new Observable(new Memory({
						data: this.entries
					}));
					this.set('store', store);
					break;
				case portalTools.RenderMode.DND:
					this.dndSource.insertNodes(false, this.entries);
					this._resizeItemNames();
					break;
			}
		},

		getRenderInfo: function(item) {
			return lang.mixin(this.inherited(arguments), {
				itemSubName: item.host_name
			});
		},

		getIconClass: function(logoUrl) {
			return portalTools.getIconClass(logoUrl);
		},

		getStatusIconClass: function(item) {
			return this.renderMode === portalTools.RenderMode.EDIT ? 'editIcon' : 'noStatus';
		},

		renderRow: function(item) {
			var domNode;
			switch (this.renderMode) {
				case portalTools.RenderMode.NORMAL:
					domNode = this.inherited(arguments);
					var link = put('a[href=$]', this._getWebInterfaceUrl(item));
					var openLinkInNewWindow = false;
					if (this.defaultLinkTarget && this.defaultLinkTarget === 'newwindow') {
						openLinkInNewWindow = true;
					}
					switch (item.linkTarget) {
						case 'samewindow':
							openLinkInNewWindow = false; break;
						case 'newwindow':
							openLinkInNewWindow = true;  break;
					}
					if (openLinkInNewWindow) {
						link.target = '_blank';
						link.rel = 'noopener';
					}
					put(domNode, link, query('.umcGalleryItem', domNode)[0]);
					break;
				case portalTools.RenderMode.EDIT:
					if (item.id && item.id === '$addEntryTile$') {
						domNode = this.getBlankTile();
						put(domNode, '.addEntryTile');
					} else if (item.id && item.id.indexOf('$entryNotInPortalJSON$') >= 0) {
						domNode = this.getBlankTile();
						put(domNode, '.notInPortalJSONTile');
					} else {
						domNode = this.inherited(arguments);
						put(domNode, '.editEntryTile');
					}
					break;
				case portalTools.RenderMode.DND:
					if (item.id && item.id.indexOf('$entryNotInPortalJSON$') >= 0) {
						domNode = this.getBlankTile();
						put(domNode, '.notInPortalJSONTile');
					} else {
						var renderInfo = this.getRenderInfo(item);
						domNode = this.getDomForRenderRow(renderInfo);
					}
					break;
			}
			domClass.toggle(domNode, 'deactivated', item.id !== '$addEntryTile$' && !item.activated);
			return domNode;
		},

		getBlankTile: function() {
			var domString = '' +
				'<div class="umcGalleryWrapperItem">' +
					'<div class="cornerPiece boxShadow bl">' +
						'<div class="hoverBackground"></div>' +
					'</div>' +
					'<div class="cornerPiece boxShadow tr">' +
						'<div class="hoverBackground"></div>' +
					'</div>' +
					'<div class="cornerPiece boxShadowCover bl"></div>' +
					'<div class="dummyIcon"></div>' +
				'</div>';
			var domNode = domConstruct.toDom(domString);
			return domNode;
		},

		// can't be used with dojo/on since this widget does not inherit from _WidgetBase
		// use dojo/aspect.after
		onAddEntry: function() {
			// event stub
		},

		onEditEntry: function(entry) {
			// event stub
		},

		onEntryNotInPortalJSON: function(entry) {
			// event stub
		},

		_getProtocolAndPort: function(app) {
			var protocol = window.location.protocol;
			var port = null;

			if (protocol === 'http:') {
				port = app.web_interface_port_http;
				if (!port && app.web_interface_port_https) {
					protocol = 'https:';
					port = app.web_interface_port_https;
				}
			} else if (protocol === 'https:') {
				port = app.web_interface_port_https;
				if (!port && app.web_interface_port_http) {
					protocol = 'http:';
					port = app.web_interface_port_http;
				}
			}

			if (port && app.auto_mod_proxy) {
				if (protocol === 'http:') {
					port = '80';
				} else if (protocol === 'https:') {
					port = '443';
				}
			}

			if (port === '80') {
				protocol = 'http:';
				port = null;
			} else if (port === '443') {
				protocol = 'https:';
				port = null;
			}
			if (port) {
				port = ':' + port;
			} else {
				port = '';
			}

			return {
				protocol: protocol,
				port: port
			};
		},

		_getWebInterfaceUrl: function(app) {
			if (!app.web_interface) {
				return "";
			}
			if (app.web_interface.indexOf('/') !== 0) {
				return app.web_interface;
			}

			var protocolAndPort = this._getProtocolAndPort(app);
			var protocol = protocolAndPort.protocol;
			var port = protocolAndPort.port;

			var fqdn = app.host_name + '.' + this.domainName;
			var host = (app.host_ips) ? getHost(app.host_ips, fqdn) : window.location.host;

			var url = lang.replace('{protocol}//{host}{port}{webInterface}', {
				protocol: protocol,
				host: host,
				port: port,
				webInterface: app.web_interface
			});

			return url;
		},

		_resizeItemNamesOfAvatarTile: function(node) {
			var offscreenWrapper = put(dojo.body(), 'div.dijitOffScreen', node, '<');
			var defaultValues = this._getDefaultValuesForResize('.umcGalleryName');
			query('.umcGalleryNameContent', node).forEach(lang.hitch(this, function(inode) {
				var fontSize = parseInt(defaultValues.fontSize, 10) || 16;
				while (domGeometry.position(inode).h > defaultValues.height) {
					fontSize--;
					domStyle.set(inode, 'font-size', fontSize + 'px');
				}
			}));
			put(offscreenWrapper, '!');
		}
	});
});
