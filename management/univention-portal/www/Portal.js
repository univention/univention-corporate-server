/*
 * Copyright 2020 Univention GmbH
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

/**
 * @module portal/Portal
 */
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/Deferred",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/when",
	"dojo/aspect",
	"dojo/on",
	"dojo/on/debounce",
	"dojo/debounce",
	"dojo/mouse",
	"dojo/query",
	"dojo/topic",
	"dojo/io-query",
	"dojo/regexp",
	"dojo/dnd/Source",
	"dojo/promise/all",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"dijit/_WidgetsInTemplateMixin",
	"dijit/form/Button", // TODO put in umc/widgets
	"dijit/form/ToggleButton", // TODO put in umc/widgets
	"dijit/DropDownMenu",
	"dijit/MenuItem",
	"dijit/form/DropDownButton",
	"dijit/a11yclick",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ConfirmDialog",
	"umc/menu",
	"umc/store",
	"umc/dialog",
	"umc/render",
	"umc/tools",
	"umc/i18n/tools",
	"put-selector/put",
	"./PortalEntryWizard",
	"./AppTile",
	"./PortalPropertiesButton",
	"./Dialog",
	"./CategoryPropertiesDialog",
	"./FolderPropertiesDialog",
	"./AddCategoryButton",
	"./AddEntryButton",
	"./links",
	"./properties",
	"./portalContent",
	"login",
	"umc/i18n!portal",
	"umc/dialog/NotificationSnackbar",
	"./_PortalIframeTabsContainer",
	"./_PortalIframesContainer",
	"./NotificationsButton",
	"./Menu",
], function(
	declare, lang, array, Deferred, domStyle, domClass, domConstruct, domAttr, when, aspect, on, onDebounce, debounce, mouse, query, topic, ioQuery, regexp,
	Source, all, _WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin, Button, ToggleButton, DropDownMenu, MenuItem,
	DropDownButton, a11yclick, Text, TextBox, ContainerWidget, ConfirmDialog, menu, store, dialog, render, tools, i18nTools,
	put, PortalEntryWizard, AppTile, PortalPropertiesButton, Dialog, CategoryPropertiesDialog, FolderPropertiesDialog, AddCategoryButton, AddEntryButton, portalLinks, properties,
	portalContent, login, _
) {
	var locale = i18nTools.defaultLang().replace(/-/, '_');

	var PortalSearchBox = declare("PortalSearchBox", [TextBox], {
		//// overwrites
		intermediateChanges: true,


		//// lifecycle
		constructor: function() {
			this.baseClass += ' portalSearchBox';
		}
	});

	var PortalMobileIframeTabsButton = declare("PortalMobileIframeTabsButton", [ToggleButton], {
		//// self
		count: '',
		_setCountAttr: function(count) {
			this.counter.innerHTML = count ? count : '';
		},


		//// lifecycle
		buildRendering: function() {
			this.inherited(arguments);
			this.counter = put(this.domNode, 'div.portal__mobileIframeTabsButton__counter');
		},
	});

	var PortalLoginMessage = declare("PortalLoginMessage", [_WidgetBase, _TemplatedMixin], {
		//// overwrites
		templateString: `
			<div class="portalLoginMessage" data-dojo-attach-point="messageNode"></div>
		`,


		//// self
		message: _('Login <a class="portalLoginMessageAction" href="#">here</a> so that you can use the full range of functions of UCS.'),
		_setMessageAttr: { node: 'messageNode', type: 'innerHTML' },

		onAction() {},


		//// lifecycle
		postCreate() {
			this.inherited(arguments);
			query('.portalLoginMessageAction', this.messageNode).on('click', () => {
				this.onAction();
			});
		},
	});

	return declare("Portal", [_WidgetBase, _TemplatedMixin, _WidgetsInTemplateMixin], {
		templateString: `
			<div class="portal">
				<div class="portal__header" data-dojo-attach-point="headerNode">
					<div
						class="portal__header__left"
						tabindex="0"
						data-dojo-attach-point="headerLeftNode"
					>
						<img
							class="dijitDisplayNone"
							alt="Portal logo"
							data-dojo-attach-point="portalLogoNode"
						>
						<h2
							data-dojo-attach-point="portalTitleNode"
						></h2>
					</div>
					<div
						class="portal__iframeTabs"
						data-dojo-type="portal/_PortalIframeTabsContainer"
						data-dojo-attach-point="iframeTabs"
					></div>
					<div class="portal__header__stretch"></div>
					<div
						class="portal__header__right"
						data-dojo-attach-point="headerRightNode"
					>
						<button
							class="portal__mobileIframeTabsButton ucsIconButton"
							data-dojo-type="PortalMobileIframeTabsButton"
							data-dojo-attach-point="mobileIframeTabsButton"
							data-dojo-props="
								iconClass: 'iconTabs',
								showLabel: false
							"
						></button>
						<button
							class="ucsIconButton"
							data-dojo-type="dijit/form/ToggleButton"
							data-dojo-attach-point="toggleSearchButton"
							data-dojo-props="
								iconClass: 'iconSearch',
								showLabel: false
							"
						></button>
						<button
							data-dojo-type="NotificationsButton"
							data-dojo-attach-point="notificationsButton"
						></button>
						<button
							class="ucsIconButton"
							data-dojo-type="dijit/form/ToggleButton"
							data-dojo-attach-point="toggleMenuButton"
							data-dojo-props="
								iconClass: 'iconMenu',
								showLabel: false
							"
						></button>
					</div>
				</div>
				<div class="portal__background" data-dojo-attach-point="portalBackgroundNode"></div>
				<div
					class="portal__categories"
					data-dojo-attach-point="categoriesNode"
				></div>
				<div
					class="portal__folder dijitDisplayNone"
					data-dojo-attach-point="foldersNode"
				></div>
				<div
					class="portal__search"
					data-dojo-attach-point="portalSearchBoxWrapperNode"
				>
					<div
						data-dojo-type="PortalSearchBox"
						data-dojo-attach-point="portalSearchBox"
					></div>
				</div>
				<div
					class="portal__iframes dijitDisplayNone"
					data-dojo-type="portal/_PortalIframesContainer"
					data-dojo-attach-point="iframesContainer"
				></div>
				<div
					class="portal__loginIframeWrapper dijitDisplayNone"
					data-dojo-attach-point="loginIframeWrapper"
				></div>
				<div
					class="portal__mobileIframeTabs overlaybg dijitDisplayNone"
					data-dojo-type="portal/_PortalIframeTabsContainer"
					data-dojo-attach-point="mobileIframeTabs"
				></div>
				<div
					data-dojo-type="PortalMenu"
					data-dojo-attach-point="portalMenu"
					data-dojo-attach-event="enterEditMode: enterEditMode"
					data-dojo-props="
						showLoginHeader: true,
						loginCallbacks: this.loginCallbacks
					"
				></div>
				<div
					class="appDescription dijitDisplayNone"
					data-dojo-attach-point="hoveredAppDescriptionNode"
				></div>
				<div data-dojo-type="umc/dialog/NotificationSnackbar"></div>
			</div>
		`,


		//// self
		// edit mode
		editMode: false,
		_setEditModeAttr: function(editMode) {
			this.editMode = editMode;
			this._refresh().then(() => {
				if (editMode) {
					this.portalPropertiesButton.load();
				}
				domClass.toggle(document.body, 'editMode', editMode);
			});
			this._set('editMode', editMode);
		},
		enterEditMode: function() {
			this.set('editMode', true);
		},
		leaveEditMode: function() {
			this.set('editMode', false);
		},
		_setupEditModeIfAuthorized: async function() {
			const canEdit = await this._checkEditAuthorization();
			if (canEdit) {
				this._setupEditMode();
			}
		},
		_checkEditAuthorization: async function() {
			try {
				const res = await tools.umcpCommand('get/modules');
				return res.modules.some(module => module.flavor === 'portals/all');
			} catch(err) {
				return false;
			}
		},
		_setupEditMode: function() {
			// require cache only here and not at the beginning of the file
			// because Replica Directory Nodes and Managed Nodes do not have
			// the univention-management-console-module-udm package installed.
			// This method is only called when it is available
			require(['umc/modules/udm/cache'], lang.hitch(this, function(cache) {
				this.portalMenu.addEnterEditModeButton();

				const container = new ContainerWidget({
					'class': 'portal__header__editMode'
				});
				container.addChild(new Text({
					'class': 'portal__header__editMode__text',
					content: _('Edit mode')
				}));
				this.portalPropertiesButton = new PortalPropertiesButton({});
				on(this.portalPropertiesButton, 'propChanged', (propName, value) => {
					this.set(propName, value);
				});
				container.addChild(this.portalPropertiesButton);
				container.addChild(new Button({
					'class': 'ucsIconButton',
					iconClass: 'iconX',
					showLabel: false,
					onClick: () => {
						this.leaveEditMode();
					}
				}));
				put(this.headerNode, container.domNode);
				container.startup();
			}));
		},
		// edit mode end


		portalLogo: null,
		_setPortalLogoAttr: function(src) {
			const origSrc = src;
			tools.toggleVisibility(this.portalLogoNode, !!src);
			if (src && !src.startsWith('data:image')) {
				src = `${src}?${Date.now()}`;
			}
			this.portalLogoNode.src = src;
			this._set('portalLogo', origSrc);
		},

		portalBackground: null,
		_setPortalBackgroundAttr: function(src) {
			const origSrc = src;
			tools.toggleVisibility(this.portalBackgroundNode, !!src);
			if (src) {
				if (!src.startsWith('data:image')) {
					src = `${src}?${Date.now()}`;
				}
				src = `url(${src})`;
			}
			domStyle.set(this.portalBackgroundNode, "background-image", src);
			this._set('portalBackground', origSrc);
		},

		portalTitle: '',
		_setPortalTitleAttr: function(title) {
			this.portalTitleNode.innerHTML = title;
			document.title = title;
			this._set('portalTitle', title);
		},

		hoveredApp: null,
		_setHoveredAppAttr: function(entry) {
			this.hoveredAppDescriptionNode.innerHTML = '';
			if (entry) {
				var header = put(this.hoveredAppDescriptionNode, 'div.appDescription__header');
				put(header, this._renderApp(entry, true));
				put(header, 'div', entry.name);
				put(this.hoveredAppDescriptionNode, 'div', entry.description);
			}
			tools.toggleVisibility(this.hoveredAppDescriptionNode, !!entry);
			this._set('hoveredApp', entry);
		},

		menuOpen: false,
		_setMenuOpenAttr: function(open) {
			if (this.menuOpen === open) {
				return;
			}
			this._set('menuOpen', open);
			this.toggleMenuButton.set('checked', open);
			if (open) {
				this.set('notificationsOpen', false);
				menu.open();
			} else {
				menu.close();
			}
		},
		_bindMenuOpenAttr: function() {
			this.toggleMenuButton.watch('checked', (_attrName, _oldChecked, checked) => {
				this.set('menuOpen', checked);
			});
			topic.subscribe('/umc/menu', action => {
				switch (action) {
					case 'open':
						this.set('menuOpen', true);
						break;
					case 'close':
						this.set('menuOpen', false);
						break;
				}
			});
		},

		notificationsOpen: false,
		_setNotificationsOpenAttr: function(notificationsOpen) {
			if (this.notificationsOpen === notificationsOpen) {
				return;
			}
			this._set('notificationsOpen', notificationsOpen);
			if (notificationsOpen) {
				this.set('menuOpen', false);
			}

			this.notificationsButton.set('checked', notificationsOpen);
			this.notificationsButton.set('open', notificationsOpen);
		},
		_bindNotificationsOpenAttr: function() {
			this.notificationsButton.watch('checked', (_attrName, _oldChecked, checked) => {
				this.set('notificationsOpen', checked);
			});
		},

		openFolder: null,
		_setOpenFolderAttr: function(folder) {
			domClass.toggle(document.body, 'scrollLess', !!folder);
			tools.toggleVisibility(this.foldersNode, !!folder);

			this.foldersNode.innerHTML = '';
			if (folder) {
				var background = put(this.foldersNode, 'div.portal__folder__overlay.overlaybg');
				on(background, 'click', evt => {
					if (evt.target === background) {
						this.set('openFolder', null);
					}
				});

				var wrapper = put(background, 'div.portal__folder__wrapper');
				var closeButton = new Button({
					showLabel: false,
					iconClass: 'iconX',
					'class': 'ucsIconButton',
					onClick: evt => {
						this.set('openFolder', null);
					}
				});
				put(wrapper, closeButton.domNode);
				var box = put(wrapper, 'div.box');
				var carrousell = put(box, 'div.carrousell');
				var slide = put(carrousell, 'div.slide')
				let counter = 0;
				let slides = 1;
				for (const entry of folder.entries) {
					const tileNode = this._renderApp(entry);
					put(slide, tileNode);
					counter++;
					if (counter === 9) {
						counter = 0;
						slides++;
						slide = put(carrousell, 'div.slide')
					}
				}

				if (slides >= 2) {
					var nav = put(box, 'div.nav');
					for (let x = 0; x < slides; x++) {
						let b = put(nav, 'div.bubble');
						if (x === 0) {
							put(b, '.bubble--active');
						}
						on(b, 'click', evt => {
							query('.bubble', nav).removeClass('bubble--active');
							put(nav.children[x], '.bubble--active');
							carrousell.style.left = ((x * 720) * -1) + 'px';
						});
					}
				}

				// TODO
				let title = 'Title';
				put(wrapper, 'h1', title);

				put(this.foldersNode, background);
			}
			this._set('openFolder', folder);
		},

		selectedIframeId: null,
		_setSelectedIframeIdAttr: function(id) {
			domClass.toggle(document.body, 'scrollLess', id);
			this.iframeTabs.set('selectedIframeId', id);
			this.iframesContainer.set('selectedIframeId', id);
			tools.toggleVisibility(this.iframesContainer, !!id);
			this._set('selectedIframeId', id);
		},

		iframes: null,
		_setIframesAttr: function(iframes) {
			this.mobileIframeTabsButton.set('count', iframes.length);
			this.iframeTabs.set('iframes', iframes);
			this.mobileIframeTabs.set('iframes', iframes);
			this.iframesContainer.set('iframes', iframes);
			if (!iframes.map(iframe => iframe.id).includes(this.selectedIframeId)) {
				this.set('selectedIframeId', null);
			}
			this._resizeIframeTabs();
			this._set('iframes', iframes);
		},

		_loginIframe: null,
		showLoginIframe: function(saml) {
			if (!this._loginIframe) {
				var target = saml ? '/univention/saml/' : '/univention/login/';
				var url = target + '?' + ioQuery.objectToQuery({
					'location': '/univention/portal/loggedin/',
					username: tools.status('username'),
					lang: i18nTools.defaultLang()
				});

				this._loginIframe = new _PortalIframe({
					iframe: {
						url: url
					}
				});

				this._loginIframe.iframeNode.addEventListener('load', () => {
					var pathname = lang.getObject('contentWindow.location.pathname', false,
							this._loginIframe.iframeNode);
					if (pathname === '/univention/portal/loggedin/') {
						login.start(null, null, true).then(() => {
							this._setupEditModeIfAuthorized();
							this._refresh();
						});
						tools.toggleVisibility(this.loginIframeWrapper, false);
						this._loginIframe.destroyRecursive();
					}
				});
				this.loginIframeWrapper.appendChild(this._loginIframe.domNode);
			}
			tools.toggleVisibility(this.loginIframeWrapper, true);
		},


		_reloadCss() {
			// FIXME? instead of reloading the portal.css file,
			// use styles.insertCssRule to display the style
			// changes made after the first site load

			// reload the portal.css file
			var re = /.*\/portal.css\??\d*$/;
			var links = document.getElementsByTagName('link');
			var link = array.filter(links, function(ilink) {
				return re.test(ilink.href);
			})[0];
			if (!link) {
				return;
			}
			var href = link.href;
			if (href.indexOf('?') !== -1) {
				href = href.substr(0, href.indexOf('?'));
			}
			href += lang.replace('?{0}', [Date.now()]);
			link.href = href;
		},

		_refresh: async function() {
			await portalContent.reload(this.editMode);
			this._reloadCss();
			this.set('portalLogo', portalContent.logo());
			this.set('portalTitle', portalContent.title());
			this.set('portalBackground', portalContent.background());
			this.set('content', portalContent.content());
			this.set('openFolder', null); // TODO rerender the correct folder on refresh, if it is still in content
			this.portalMenu.addLinks(); // TODO old links have to be removed if portalContent.links() changes.
		},

		content: null,
		_filteredContent: null,
		_set_filteredContentAttr: function(_filteredContent) {
			this.categoriesNode.innerHTML = '';
			this.dndSource = null;
			if (this.editMode) {
				this.dndSource = new Source(this.categoriesNode, {
					copyState: function() {
						return false; // do not allow copying
					},
					type: ['PortalCategories'],
					accept: ['PortalCategory'],
					withHandles: true,
					creator: lang.hitch(this, function(item, hint) {
						if (hint === 'avatar') {
							return { node: this._renderCategory(item, true) }; 
						}

						return {
							node: this._renderCategory(item),
							data: item,
							type: ['PortalCategory']
						};
					})
				});
				this.dndSource.insertNodes(false, _filteredContent);
				const onDndStartHandler = aspect.after(this.dndSource, 'onDndStart', lang.hitch(this, function(source) {
					if (source === this.dndSource) {
						domClass.add(this.categoriesNode, 'draggingCategory');
					}
				}), true);
				const onDndCancelHandler = aspect.after(this.dndSource, 'onDndCancel', lang.hitch(this, function() {
					domClass.remove(this.categoriesNode, 'draggingCategory');
				}));


				const button = new AddCategoryButton({});
				put(this.categoriesNode, button.domNode);
			} else {
				for (const category of _filteredContent) {
					const categoryNode = this._renderCategory(category);
					put(this.categoriesNode, categoryNode);
				}
			}
			window.requestAnimationFrame(function() {
				for (const titleNode of document.querySelectorAll('.tile__name')) {
					if (titleNode.scrollWidth > titleNode.clientWidth) {
						titleNode.title = titleNode.innerHTML;
					} else {
						titleNode.title = '';
					}
				}
			});
			this._set('_filteredContent', _filteredContent);
		},
		_compute_filteredContent: function() {
			if (!this.searchActive || !this.searchTerm) {
				return this.content;
			} else {
				let searchTerm = regexp.escapeString(this.searchTerm);
				searchTerm = searchTerm.replace(/\\\*/g, '.*');
				searchTerm = searchTerm.replace(/ /g, '\\s+');
				const re = new RegExp(searchTerm, 'i');
				const matchesSearch = (entry, re) => re.test(entry.name) || re.test(entry.description);

				return this.content.map(category => {
					const newCat = { ...category }; // shallow copy
					newCat.entries = newCat.entries.map(entry => {
						if (entry.type === 'entry') {
							return entry;
						} else {
							const newFolder = { ...entry }; // shallow copy
							newFolder.entries = newFolder.entries.filter(entry => {
								return matchesSearch(entry, re);
							});
							return newFolder;
						}
					}).filter(entry => {
						if (entry.type === 'entry') {
							return matchesSearch(entry, re);
						} else {
							return entry.entries.length > 0;
						}
					});
					return newCat;
				}).filter(category => {
					return category.entries.length > 0;
				});
			}
		},
		_bind_filteredContentAttr: function() {
			for (const name of ['searchActive', 'content', 'searchTerm']) {
				this.watch(name, () => {
					this.set('_filteredContent', this._compute_filteredContent());
				});
			}
		},


		editFolder: function(folder) {
			const dialog = new FolderPropertiesDialog({
				folder,
				parentDn: folder.parentDn,
			});
			dialog.showAndLoad();
		},

		editCategory: function(category) {
			const dialog = new CategoryPropertiesDialog({
				category,
			});
			dialog.showAndLoad();
		},


		_renderCategory: function(category, asDndAvatar) {
			const categoryNode = put('div[id=$].portal__category', category.id);

			if (this.editMode) {
				var node = put(categoryNode,
					`h2.portal__category__title.portal__category__title--edit.dojoDndHandle
					 div.portal__category__title__editMark.editMark.iconEdit < $`,
					category.title);
				on(node, 'click', () => {
					this.editCategory(category);
				});
			} else {
				put(categoryNode, 'h2.portal__category__title', category.title);
			}
			if (asDndAvatar) {
				return categoryNode;
			}

			const tilesNode = put(categoryNode, 'div.portal__category__tiles');
			if (this.editMode) {
				put(tilesNode, '.portal__category__tiles--dnd');
				const dndSource = new Source(tilesNode, {
					type: ['PortalEntries'],
					accept: ['PortalEntry'],
					copyState: function() {
						return false; // do not allow copying
					},
					creator: (item, hint) => {
						const node = item.type === 'entry'
							? this._renderApp(item)
							: this._renderFolder(item);

						if (hint === 'avatar') {
							return { node: node };
						}

						return {
							// node: put('div', node), // wrap the tile so that the margin is part of the node and there is is no gap between the tiles
							node: node,
							data: item,
							type: ['PortalEntry']
						};
					},
				});
				dndSource.insertNodes(false, category.entries);
				categoryNode.dndSource = dndSource;


				const dndPlaceholder = domConstruct.toDom('' +
					'<div class="dndPlaceholder dojoDndItem tile__dotted">' +
					'</div>'
				);
				const dndPlaceholderHideout = put(tilesNode, 'div.dndPlaceholderHideout');
				put(dndPlaceholderHideout, dndPlaceholder);
				//// move the dndPlaceholder around
				aspect.after(dndSource, '_addItemClass', lang.hitch(this, function(target, cssClass) {
					if (dndSource.isDragging) {
						if (target === dndPlaceholder) {
							return;
						}

						// if the placeholder tile is not placed yet, ...
						if (dndPlaceholderHideout.firstChild === dndPlaceholder) {
							// and we come from outside the dndSource,
							// place the placeholder in place of hovered tile
							if (!dndSource.current && dndSource.anchor /* check for anchor to see if we are in the same category as the dragged tile */) {
								var putCombinator = query(lang.replace('#{0} ~ #{1}', [dndSource.anchor.id, target.id]), dndSource.parent).length ? '+' : '-';
								put(target, putCombinator, dndPlaceholder);
							} else {
								// this case is when the drag event is started.
								// Put the placeholder in the place of the dragged tile
								put(target, '-', dndPlaceholder);
							}
							return;
						}

						// if we hover over a different tile while dragging and while the placeholder tile is placed
						// we move the placeholder tile to the hovered tile
						if (cssClass === 'Over') {
							// if we hover a tile to the right of the placeholder we want to place the placeholder to the right of the hovered tile
							// and vice versa
							var putCombinator = query(lang.replace('#{0} ~ .dndPlaceholder', [target.id]), dndSource.parent).length ? '-' : '+';
							put(target, putCombinator, dndPlaceholder);
						}
					}
				}), true);
				// when we are dragging a tile but are not hovering over a different tile
				// then we want to add the dndPlaceholder at the end of the gallery
				aspect.after(dndSource, 'onMouseMove', lang.hitch(this, function() {
					if (!dndSource.isDragging) {
						return;
					}
					const lastChild = dndSource.parent.children[dndSource.parent.childElementCount-3];
					if (!dndSource.current && lastChild !== dndPlaceholder) {
						// put(dndSource.parent, dndPlaceholder);
						put(lastChild, '+', dndPlaceholder);
					}
				}));

				//// put the dndPlaceholder back into dndPlaceholderHideout
				aspect.before(dndSource, 'onDropInternal', lang.hitch(this, function() {
					const lastChild = dndSource.parent.children[dndSource.parent.childElementCount-3];
					if (!dndSource.current && lastChild === dndPlaceholder) {
						dndSource.current = dndPlaceholder.previousSibling;
					}
				}));
				aspect.after(dndSource, 'onDndCancel', lang.hitch(this, function() {
					put(dndPlaceholderHideout, dndPlaceholder);
				}));
				aspect.after(dndSource, 'onDraggingOut', lang.hitch(this, function() {
					put(dndPlaceholderHideout, dndPlaceholder);
				}));





				const b = new AddEntryButton({
					parentDn: category.dn,
				});
				on(b, 'createNewEntry', () => {
					this.editPortalEntry(category.dn);
				});
				put(tilesNode, b.domNode);
			} else {
				for (const entry of category.entries) {
					const tileNode = entry.type === 'entry'
						? this._renderApp(entry)
						: this._renderFolder(entry);
					put(tilesNode, tileNode);
				}
			}
			return categoryNode;
		},

		_renderApp: function(entry, asThumbnail) {
			const { dn, name, href, bgc, logo, linkTarget } = entry;

			if (asThumbnail) {
				const _tileNode = `
					<div
						class="tile__box--thumbnail"
						style="background: ${bgc}"
					>
						<img 
							class="tile__logo"
							src="${logo}"
							alt="${name} logo"
						>
					</div>
				`.trim();
				const tileNode = domConstruct.toDom(_tileNode);

				return tileNode;
			} else {
				const _tileNode = `
					<div class="tile app">
						<div
							class="tile__box"
							style="background: ${bgc}"
						>
							<img 
								class="tile__logo"
								src="${logo}"
								alt="${name} logo"
							>
						</div>
						<span class="tile__name">${name}</span>
					</div>
				`.trim();
				const tileNode = domConstruct.toDom(_tileNode);
				const tileLink = put('a.tileLink[href=$][draggable="true"]', href, tileNode);
				if (this.editMode) {
					put(tileNode, 'div.tile__editMark.editMark.iconEdit');
					tileNode.onclick = evt => {
						evt.preventDefault();
						this.editPortalEntry(entry.parentDn, entry.dn, entry.idx);
					};
				} else {
					switch (linkTarget) {
						case 'samewindow':
							break;
						case 'newwindow':
							tileLink.target = '_blank';
							tileLink.rel = 'noopener';
							break;
						case 'embedded':
							tileLink.onclick = function(evt) {
								evt.preventDefault();
								topic.publish('/portal/iframes/open', dn, name, logo, href);
							};
							break;
					}
				}


				on(tileLink, 'focus', evt => {
					this.set('hoveredApp', entry);
				});
				on(tileLink, 'blur', evt => {
					this.set('hoveredApp', null);
				});
				on(tileLink, 'mouseenter', evt => {
					this.set('hoveredApp', entry);
				});
				on(tileLink, 'mouseleave', evt => {
					this.set('hoveredApp', null);
				});
				return tileLink;
			}
		},

		_renderFolder: function(folder) {
			const { dn, name } = folder;

			const _folderNode = `
				<div class="tile">
					<div
						class="tile__box tile__box--folder"
					>
						<div class="tile__thumbnails"></div>
					</div>
					<span class="tile__name">${name}</span>
				</div>
			`.trim();
			const folderNode = domConstruct.toDom(_folderNode);

			const container = folderNode.querySelector('.tile__thumbnails');
			for (let x = 0; x < Math.min(folder.entries.length, 9); x++) {
				const thumbnailNode = this._renderApp(folder.entries[x], true);
				put(container, thumbnailNode);
			}

			if (this.editMode) {
				const editMarkNode = put('div.tile__editMark.editMark.iconEdit');
				put(folderNode, editMarkNode);
				editMarkNode.onclick = evt => {
					evt.stopImmediatePropagation();
					evt.preventDefault();
					this.editFolder(folder);
				};
			}
			on(folderNode, 'click', evt => {
				this.set('openFolder', folder);
			});
			return folderNode;
		},

		constructor: function() {
			this.loginCallbacks = {
				login: () => {
					const hideStandby = this.standby();
					login.start(null, null, true, (saml) => {
						hideStandby();
						this.showLoginIframe(saml);
					});
				}
			};
			this.saveEntryOrderDebounced = debounce(this.saveEntryOrder, 3000);
			this.iframes = [];
			this.portalLogo = portalContent.logo();
			this.portalTitle = portalContent.title();
			this.portalBackground = portalContent.background();
			this.content = portalContent.content();
		},

		searchTerm: '',
		_setSearchTermAttr: function(searchTerm) {
			this.portalSearchBox.set('value', searchTerm);
			this._set('searchTerm', searchTerm);
		},
		_bindSearchTermAttr: function() {
			on(this.portalSearchBox, 'change', searchTerm => {
				if (searchTerm !== this.searchTerm) {
					this.set('openFolder', null); // FIXME better spot?
					this._changeAttrValue('searchTerm', searchTerm);
				}
			});
		},

		showMobileIframeTabs: false,
		_setShowMobileIframeTabsAttr: function(showTabs) {
			domClass.toggle(document.body, 'scrollLess', showTabs);
			tools.toggleVisibility(this.mobileIframeTabs, showTabs);

			this.mobileIframeTabsButton.set('checked', showTabs);
			domClass.toggle(this.mobileIframeTabs, 'portal__mobileIframeTabs--open', showTabs);
			this._set('showMobileIframeTabs', showTabs);
		},
		_bindShowMobileIframeTabsAttr: function() {
			this.mobileIframeTabsButton.watch('checked', (_attrName, _oldChecked, checked) => {
				this.set('showMobileIframeTabs', checked);
				// TODO _changeAttrValue
			});
			// TODO should this be closeable in a different way too
		},

		searchActive: false,
		_setSearchActiveAttr: function(searchActive) {
			if (searchActive) {
				this.set('showMobileIframeTabs', false);
				this.set('menuOpen', false);

				this.set('selectedIframeId', null);
			}

			this.toggleSearchButton.set('checked', searchActive);
			domClass.toggle(this.portalSearchBoxWrapperNode, 'portal__search--open', searchActive);
			this.portalSearchBox.set('disabled', !searchActive);
			if (searchActive) {
				this.portalSearchBox.focus();
			}
			this._set('searchActive', searchActive);
		},
		_bindSearchActiveAttr: function() {
			this.toggleSearchButton.watch('checked', (_attrName, _oldChecked, checked) => {
				this.set('searchActive', checked);
				// TODO _changeAttrValue?
			});
			on(this.portalSearchBox, 'keyup', evt => {
				if (evt.key === "Escape") {
					this.set('searchActive', false);
				}
			});
		},

		mobileTabsView: false,
		_setMobileTabsViewAttr: function(isTrue) {
			tools.toggleVisibility(this.iframeTabs, !isTrue);
			tools.toggleVisibility(this.mobileIframeTabsButton, isTrue);
			this._set('mobileTabsView', isTrue);
		},

		standby() {
			return tools.standby(this, {zIndex: 1000});
		},


		postCreate: function() {
			this.inherited(arguments);

			this._setupEditModeIfAuthorized();

			// iframes, selectedIframeId
			on(this.headerLeftNode, a11yclick, () => {
				this.set('selectedIframeId', null);
			});
			topic.subscribe('/portal/iframes/open', (id, title, logoUrl, url) => {
				this.set('iframes', [
					...this.iframes,
					{
						id,
						title,
						logoUrl,
						url
					}
				]);
				this.set('selectedIframeId', id);
			});
			topic.subscribe('/portal/iframes/close', id => {
				this.set('iframes', this.iframes.filter(iframe => iframe.id !== id));
			});
			topic.subscribe('/portal/iframes/select', id => {
				this.set('showMobileIframeTabs', false);
				this.set('selectedIframeId', id);
			});
			// iframes, selectedIframeId end


			// dnd
			topic.subscribe('/dnd/drop', () => {
				this.saveEntryOrderDebounced();
			});
			// dnd end


			portalContent.subscribeRefresh(() => {
				this._refresh();
			});
			on(window, onDebounce('resize', 200), () => {
				this.resize();
			});

			this.portalMenu.addLinks();

			// show login notification if not logged in
			// TODO is there a better way to know if someone isnt logged in
			// i guess tools.status('loggedIn') should work but there can be timing problems
			login.sessioninfo().then().otherwise(() => {
				this.notificationsButton.addNotification({
					title: _('Login'),
					content: {
						$factory$: PortalLoginMessage,
						onAction: function() {
							this.loginCallbacks.login();
							this.notificationsButton.advance();
						}.bind(this),
					},
				});
			});
		},

		startup: function() {
			this.inherited(arguments);
			this.resize();
		},

		resize: function() {
			this._resizeIframeTabs();
		},

		_resizeIframeTabs: function() {
			this.set('mobileTabsView', this.iframeTabs.domNode.scrollWidth > this.iframeTabs.domNode.clientWidth);
		},

		_applyAttributes: function() {
			this.inherited(arguments);
			const prefix = '_compute';
			for (const name in this.constructor.prototype) {
				if (name.startsWith(prefix)) {
					const attrName = name.substring(prefix.length);
					this.set(attrName, this[name]());
				}
			}
			for (const name in this.constructor.prototype) {
				if (name.startsWith('_bind')) {
					this[name]();
				}
			}
		},



		_isEmptyValue: function(value) {
			if (typeof value === 'string' || value instanceof Array) {
				return value.length === 0;
			} else if (typeof value === 'object') {
				return Object.keys(value).length === 0;
			} else {
				return false;
			}
		},
		//// TODO refactor
		// editPortalEntry: function(portalCategory, item) {
		editPortalEntry: function(parentDn, entryDn, entryIdx) {
			// TODO copy pasted partially from udm/DetailPage - _prepareWidgets
			var _prepareProps = function(props) {
				array.forEach(props, function(iprop) {
					if (iprop.type.indexOf('MultiObjectSelect') >= 0) {
						iprop.multivalue = false;
						iprop.umcpCommand = store('$dn$', 'udm', 'portals/all').umcpCommand;
					} else if (iprop.multivalue && iprop.type !== 'MultiInput') {
						iprop.subtypes = [{
							type: iprop.type,
							dynamicValues: iprop.dynamicValues,
							dynamicValuesInfo: iprop.dynamicValuesInfo,
							dynamicOptions: iprop.dynamicOptions,
							staticValues: iprop.staticValues,
							size: iprop.size,
							depends: iprop.depends
						}];
						iprop.type = 'MultiInput';
					}
				});
				return props;
			};

			var hideStandby = tools.standby(document.body);
			var _initialDialogTitle = entryDn ? _('Edit entry') : _('Create entry');

			properties._udmCache().then(lang.hitch(this, function(_cache) {

			_cache.getProperties('portals/entry').then(lang.hitch(this, function(portalEntryProps) {
				portalEntryProps = lang.clone(portalEntryProps);

				render.requireWidgets(portalEntryProps).then(lang.hitch(this, function() {
					portalEntryProps = _prepareProps(portalEntryProps);
					var wizardWrapper = new ContainerWidget({});
					var tile = new AppTile({});
					var wizard = new PortalEntryWizard({
						portalEntryProps: portalEntryProps,
						moduleStore: portalContent.udmStore(),
						locale: locale,
					});
					var wizardDialog = null;

					wizard.own(on(wizard, 'loadEntry', function() {
						// FIXME this is not really clear
						// if we click on a tile of an existing portal entry,
						// loadEntry is called before the wizardDialog exists.
						// This case is for when we click on the tile
						// to create a new portal entry and then load an
						// existing entry by entering an existing portal entry name.
						if (wizardDialog) {
							wizardDialog._initialTitle = _('Edit entry');
						}
						// // TODO
						// domClass.toggle(tile.domNode, 'editMode', wizard.dn ? true : false);
						// on(tile.domNode, mouse.enter, function() {
							// domClass.add(tile.wrapperNode, 'hover');
						// });
						// on(tile.domNode, mouse.leave, function() {
							// domClass.remove(tile.wrapperNode, 'hover');
						// });
						//
					}));
					wizard.startup();
					wizard.ready().then(lang.hitch(this, function() {
						// adjust wizardDialog title when the page of the wizard changes
						tile.set('currentPageClass', wizard.selectedChildWidget.name);
						wizard.own(wizard.watch('selectedChildWidget', function(name, oldPage, newPage) {
							// focus the first focusable element for the current page
							wizardDialog.focus();

							tile.set('currentPageClass', newPage.name);
							var subtext = {
								'icon': ': Icon',
								'displayName': ': Display Name',
								'link': ': Link',
								'description': ': Description',
								'name': ''
							}[newPage.name];
							wizardDialog.set('title', lang.replace('{0}{1}', [wizardDialog._initialTitle, subtext]));
						}));


						// watch the icon on the icon page and update the preview tile accordingly
						wizard.getWidget('icon')._image.watch('value', function(name, oldVal, newVal) {
							var iconUri = '';
							if (newVal) {
								iconUri = lang.replace('data:image/{0};base64,{1}', [this._getImageType(), newVal]);
							}
							tile.set('icon', iconUri);
						});

						wizard.getWidget('backgroundColor').intermediateChanges = true;
						wizard.getWidget('backgroundColor').watch('value', (_name, _oldVal, newVal) => {
							tile.set('backgroundColor', newVal);
						});

						// add onChange listener for displayName and description
						// to update the preview tile if displayName or description
						// is changed
						// var defaultValuesForResize = this._portalCategories[0].grid._getDefaultValuesForResize('.umcGalleryName'); // TODO remove?
						array.forEach(['displayName'], function(ipropName) {
							var widget = wizard.getWidget(ipropName);
							widget.ready().then(function() {
								array.forEach(widget._widgets, function(iwidget) {
									iwidget[1].set('intermediateChanges', true);
									wizard.own(on(iwidget[1], 'change', function() {
										var previewText = '';
										var ipropValues = widget.get('value');
										// ipropValues has the following format where
										// the current locale (selected language for the portal)
										// is the first entry
										//   [
										//   	['de_DE', 'Text']
										//   	['fr_FR', '']
										//   	['en_EN', 'Text']
										//   ]
										//
										// if text for current locale exists
										// we use it for the preview tile else
										// we use the first locale with text
										if (ipropValues[0][1].length) {
											previewText = ipropValues[0][1];
										} else {
											// FIXME use some short circuiting
											var ipropValuesWithText = array.filter(ipropValues, function(ipropValue) {
												return ipropValue[1];
											});
											if (ipropValuesWithText.length) {
												previewText = ipropValuesWithText[0][1];
											}
										}
										tile.set(ipropName, previewText);
										// resize the displayName // TODO remove
										// if (ipropName === 'displayName') {
											// var fontSize = parseInt(defaultValuesForResize.fontSize, 10) || 16;
											// domStyle.set(tile.displayNameNode, 'font-size', fontSize + 'px');
											// while (domGeometry.position(tile.displayNameNode).h > defaultValuesForResize.height) {
												// fontSize--;
												// domStyle.set(tile.displayNameNode, 'font-size', fontSize + 'px');
											// }
										// }
									}));
								});
							});
						});

						//// listener for save / finish / cancel
						// close wizard on cancel
						wizard.own(on(wizard, 'cancel', lang.hitch(this, function() {
							wizardDialog.hide();
						})));

						// create a new portal entry object
						wizard.own(on(wizard, 'finished', lang.hitch(this, function(values) {
							wizardDialog.standby(true);

							// TOOD FIXME activated is in the wizard
							// lang.mixin(values, {
								// activated: true,
							// });

							portalContent.modify('entry', 'add', values, {objectType: 'portals/entry'}, parentDn).then(() => {
								wizardDialog.hide();
							}, () => {
								wizardDialog.standby(false);
							});
						})));

						// save changes made to an existing portal entry object
						wizard.own(on(wizard, 'save', lang.hitch(this, function(formValues) {
							wizardDialog.standby(true);

							// TODO the error message from the backend if the internal name was
							// altered is not really expressive
							var alteredValues = {};
							tools.forIn(formValues, function(iname, ivalue) {
								if (iname === '$dn$') {
									return;
								}
								if (!tools.isEqual(ivalue, wizard.initialFormValues[iname])) {
									alteredValues[iname] = ivalue;
								}
							});

							var alteredValuesNonEmpty = {};
							tools.forIn(alteredValues, function(iname, ivalue) {
								if (!this._isEmptyValue(ivalue)) {
									alteredValuesNonEmpty[iname] = ivalue;
								}
							}, this);

							// check if the values in the form have changed
							// and we do not force saving.
							// In that case return and close without saving
							if (!wizard._forceSave && Object.keys(alteredValues).length === 0) {
								wizardDialog.hide().then(function() {
									wizardDialog.destroyRecursive();
								});
								return;
							}

							//// save the altered values
							// concatenate the altered form values for displayName and description
							// with the ones filtered out when loading the portal entry object
							array.forEach(['displayName', 'description'], lang.hitch(this, function(ipropName) {
								if (alteredValues[ipropName]) {
									alteredValues[ipropName] = alteredValues[ipropName].concat(wizard.initialFormValues[ipropName + '_remaining']);
								}
							}));

							// save changes
							var putParams = lang.mixin(alteredValues, {
								'$dn$': wizard.dn
							});
							wizard.moduleStore.put(putParams).then(lang.hitch(this, function(result) {
								// see whether creating the portal entry was successful
								if (result.success) {
									// TODO reimplement
									// if the icon for the entry was changed we want a new iconClass
									// to display the new icon
									// if (formValues.icon) {
										// var entry = array.filter(portalJson.entries, function(ientry) {
											// return ientry.dn === wizard.dn;
										// })[0];
										// if (entry) {
											// portalTools.requestNewIconClass(entry.logo_name);
										// }
									// }

									// reload categories and close wizard dialog
									dialog.contextNotify(_('Changes to entry saved'), {type: 'success'});
									wizardDialog.hide();
								} else {
									dialog.alert(_('The editing of the portal entry object failed: %(details)s', result));
									wizardDialog.standby(false);
								}
								return result.success;
							}), function() {
								dialog.alert(_('The editing of the portal entry object failed.'));
								wizardDialog.standby(false);
								return false;
							}).then(lang.hitch(this, function(success) {
								if (!success) {
									return;
								}
								if (!entryDn) {
									portalContent.addEntry(parentDn, wizard.dn).then(() => {
										this._refresh();
									});
								} else {
									this._refresh();
								}
							}));
						})));

						// remove portal entry object from this portal
						wizard.own(on(wizard, 'remove', lang.hitch(this, function() {
							portalContent.removeEntry(parentDn, entryIdx).then(() => {
								wizardDialog.hide();
								this._refresh();
							});
						})));

						// create and show dialog with the wizard
						wizardWrapper.addChild(tile);
						wizardWrapper.addChild(wizard);

						var wizardReady = entryDn ? wizard.loadEntry(entryDn) : true;
						when(wizardReady).then(function() {
							wizardDialog = new Dialog({
								_initialTitle: _initialDialogTitle,
								title: _initialDialogTitle,
								'class': 'portalEntryDialog',
								content: wizardWrapper,
								destroyAfterHide: true,
								wizard: wizard,
							});
							on(wizard, 'nameQuery', function() {
								wizardDialog.standby(true);
							});
							on(wizard, 'nameQueryEnd', function() {
								wizardDialog.standby(false);
							});
							on(wizard, 'entryLoaded', function() {
								wizardDialog.standby(false);
							});
							on(wizard, 'switchPage', () => {
								wizardDialog.reposition();
							});
							wizardDialog.show();
							hideStandby();
						});
					}));
				}));
			}));

			}));
		},


		saveEntryOrder() {
			if (!this.dndSource) {
				return;
			}
			// TODO put some of it in portalContent
			// TODO return when nothing changed
			const changes = [];

			const portalChange = {
				$dn$: portalContent.portal().dn,
				categories: [],
			};
			this.dndSource.getAllNodes().forEach(node => {
				const categoryDn = this.dndSource.getItem(node.id).data.dn;
				portalChange.categories.push(categoryDn);

				const categoryChange = {
					$dn$: categoryDn,
					entries: [],
				};
				node.dndSource.getAllNodes().forEach(entryNode => {
					const entryDn = node.dndSource.getItem(entryNode.id).data.dn;
					categoryChange.entries.push(entryDn);
				});
				changes.push(categoryChange);
			});
			changes.push(portalChange);

			const deferred = [];
			for (const change of changes) {
				if (change.$dn$ === portalContent.portal().dn) {
					const oldCategories = portalContent.portal().categories; 
					if (!tools.isEqual(oldCategories, change.categories)) {
						deferred.push(portalContent.udmStore().put(change));
					}
				} else {
					const oldEntries = portalContent._portalJson.categories[change.$dn$].entries;
					if (!tools.isEqual(oldEntries, change.entries)) {
						deferred.push(portalContent.udmStore().put(change));
					}
				}
			}
			all(deferred).then(result => {
				// this._refresh();
				if (result.every(res => res.success)) {
					dialog.contextNotify(_('Order saved'), {type: 'success'});
				} else {
					dialog.alert(_('Saving entry order failed'));
				}
			});
		},
	});
});
