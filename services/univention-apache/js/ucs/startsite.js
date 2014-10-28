/*
 * Copyright 2013-2014 Univention GmbH
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
/*global define require console window $*/

define([
	"dojo/io-query",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/query",
	"dojo/dom",
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/on",
	"dojo/router",
	"dojo/hash",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/DropDownButton",
	"dijit/DropDownMenu",
	"./CategoryButton",
	"./text!/ucs-overview/entries.json",
	"./text!/ucs-overview/languages.json",
	"./i18n!../ucs"
], function(ioQuery, lang, kernel, array, query, dom, domConstruct, domAttr, domStyle, domClass, on, router, hash, Menu, MenuItem, DropDownButton, DropDownMenu, CategoryButton, entries, availableLocales, _) {
	// short cut
	var ucr = entries.ucr;

	// make sure that en-US exists
	var existsEnUsLocale = array.some(availableLocales, function(ilocale) {
		return ilocale.id == 'en-US';
	});
	if (!existsEnUsLocale) {
		availableLocales.push({
			id: 'en-US',
			label: 'English'
		});
	}

	return {
		servicesButton: null,
		adminButton: null,
		_entries: entries,
		_ucr: ucr,
		_availableLocales: availableLocales,
		_localeLang: kernel.locale.split('-')[0],
		_localeWithUnderscore: kernel.locale.replace('-', '_'),

		_localizeString: function(str) {
			if (typeof str == 'string') {
				return str;
			}
			if (typeof str != 'object') {
				// not an object
				return '';
			}

			// try several variations in order to find a proper
			// localized string
			var result = '';
			array.forEach([
				this._localeWithUnderscore, // e.g., str['de_DE']
				kernel.locale,        // e.g., str['de-DE']
				this._localeLang,           // e.g., str['de']
				'C'                   // 'C' as generic fallback
			], function(ikey) {
				if (str[ikey] && result === '') {
					result = str[ikey];
				}
			});
			return result;
		},

		_getLinkEntry: function(props, category) {
			var localizedProps = {
				category: category
			};
			array.forEach(['link', 'icon', 'label', 'description'], lang.hitch(this, function(ikey) {
				localizedProps[ikey] = this._localizeString(props[ikey]);
			}));
			//console.log(localizedProps);
			var node = domConstruct.toDom(lang.replace(
				'<div class="umcGalleryWrapperItem col-xxs-12 col-xs-6 col-sm-6 col-md-4">\n'
				+ '	<a href="{link}">\n'
				+ '		<div class="umcGalleryItem umcGalleryCategory-{category}">\n'
				+ (localizedProps.icon ? '			<div class="umcGalleryIcon" style="background-image:url({icon})"></div>\n' : '')
				+ '			<div class="umcGalleryName">{label}</div>\n'
				+ '			<div class="umcGalleryDescription">{description}</div>\n'
				+ '		</div>\n'
				+ '	</a>\n'
				+ '</div>\n',
				localizedProps
			));
			return node;
		},

		_getLinkEntries: function(category) {
			if (!this._entries[category]) {
				return [];
			}
			return array.map(this._entries[category], lang.hitch(this, function(ientry) {
				return this._getLinkEntry(ientry, category);
			}));
		},

		_placeLinkEntriesInDom: function(category) {
			var listNode = query(lang.replace('#{0}-tab', [category]))[0];
			array.forEach(this._getLinkEntries(category), lang.hitch(this, function(ientryNode) {
				domConstruct.place(ientryNode, listNode);
			}));
		},

		_focusTab: function(category) {
			// set visibility of tabs through css and also set 'selectd' of category buttons
			domClass.toggle("service-tab", "galleryTabInvisible", category != "service");
			this.servicesButton.set('selected', category == "service");
			domClass.toggle("admin-tab", "galleryTabInvisible", category == "service");
			this.adminButton.set('selected', category != "service");
		},

		_focusAdminTab: function() {
			if (!this._entries.service.length) {
				this._focusTab('admin');
			}
		},

//		_updateActiveTab: function() {
//			var hash = window.location.hash;
//			if (!hash || hash == '#') {
//				return;
//			}
//			var activeNode = query(lang.replace('#site-header .nav-tabs a[href={0}]', [hash]));
//			var nodeExists = activeNode.length > 0;
//			if (!nodeExists) {
//				return;
//			}
//			var category = hash.replace('#', '');
//			this._focusTab(category); 
//			
//		},

		_placeCategoryButtons: function(){
			this.adminButton = new CategoryButton({
				label: 'Administration',
				'class': 'category-admin',
				onClick: lang.hitch(this, function() {
					router.go('admin');
				}),
				color: '#80b828',
				categoryID: 'admin',
				iconClass: 'category-admin'
			});
			this.servicesButton = new CategoryButton({
				label: 'Web-Services',
				'class': 'category-services',
				onClick: lang.hitch(this, function() {
					router.go('service');
				}),
				color: '#4bbfef',
				categoryID: 'web',
				iconClass: 'category-services'
			});
			this.servicesButton.placeAt("category-bar");
			this.adminButton.placeAt("category-bar");
		},

		_hasServiceEntries: function() {
			return this._getLinkEntries().length;
		},

		_updateNoServiceHint: function() {
			domClass.toggle('no-service', 'dijitHidden', this._hasServiceEntries());
		},

		_updateHeader: function() {
			domClass.remove('title', 'dijitHidden');
		},

		_updateLinkEntries: function() {
			this._placeLinkEntriesInDom('admin');
			this._placeLinkEntriesInDom('service');
			this._focusAdminTab();
			this._updateNoServiceHint();
		},

		_updateNoScriptElements: function() {
			var dropdown = query('#header-right .dropdown')[0];
			var navtabs = query('#site-header .nav-tabs')[0];
			domStyle.set(dropdown, 'display', 'inherit');
			domStyle.set(navtabs, 'display', 'inherit');
		},

		_matchLocale: function(locale, /* Function? */ mapper) {
			mapper = mapper || function(i) { return i; };
			var result = null;
			array.some(this._availableLocales, function(ilocale) {
				if (mapper(locale) == mapper(ilocale.id)) {
					result = ilocale;
					return true;
				}
			});
			return result;
		},

		_updateCurrentLocale: function() {
			var buttonCurrentLocale = query('#header-right .btn-default .button-text')[0];
			// mapper function -> translate locale (e.g, en-US) to lang (e.g., en)
			var _localeLang = function(locale) {
				return locale.split('-')[0];
			};

			// find the correct locale
			array.some([null, _localeLang], function(ifunc) {
				var locale = this._matchLocale(kernel.locale, ifunc);
				if (locale) {
					domAttr.set(buttonCurrentLocale, 'innerHTML', locale.label);
					return true; // break
				}
			}, this);
		},

		_updateLocales: function() {
			this._updateCurrentLocale();
			this._updateAvailableLocales();
		},

		_updateTranslations: function() {
			query('*[data-i18n]').forEach(lang.hitch(this, function(inode) {
				var value = domAttr.get(inode, 'data-i18n');
				var translation = _(value, ucr);
				domAttr.set(inode, 'innerHTML', translation);
			}));
			query('a[href]').forEach(lang.hitch(this, function(inode) {
				var href = domAttr.get(inode, 'href');
				var translation = _(href);
				domAttr.set(inode, 'href', translation);
			}));
		},

		_registerRouter: function(){
			router.register(":category", lang.hitch(this, function(data){
				this._focusTab(data.params.category);
			}));
		},

		_createLanguagesDropDown: function(){
			var _languagesMenu = new DropDownMenu({ style: "display: none;"});
			array.forEach(this._availableLocales, function(ilocale) {
				var newMenuItem = new MenuItem ({
					label: ilocale.label,
					id: ilocale.id,
					onClick: function(){
						if (ilocale.id != dojo.locale){
							window.location.search = '?lang=' + ilocale.id;
						}
					}
				});
				_languagesMenu.addChild(newMenuItem);
			});
			var _toggleButton = new DropDownButton({
				label: _("Language"),
				name: "languages",
				dropDown: _languagesMenu,
				id: "languagesDropDown"
			});
			dom.byId("dropDownButton").appendChild(_toggleButton.domNode);
		},

		start: function() {
			this._placeCategoryButtons();
			this._registerRouter();
			//this._updateNoScriptElements();
			this._updateHeader();
			this._updateLinkEntries();
			this._updateTranslations();
			this._createLanguagesDropDown();
			if (!this._hasServiceEntries()) {
				router.startup("admin");
			} else {
				router.startup("service");
			}
		}
	};
});

