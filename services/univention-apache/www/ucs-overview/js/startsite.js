/*
 * Copyright 2013 Univention GmbH
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
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/on",
	"dojo/json",
	"dojo/text!entries.json",
	"dojo/text!languages.json",
	"/ucs-overview/js/i18n!js"
], function(ioQuery, lang, kernel, array, query, domConstruct, domAttr, domStyle, domClass, on, json, entriesStr, languagesStr, _) {
	var entries = json.parse(entriesStr);
	var ucr = entries.ucr;

	// make sure that en-US exists
	var availableLocales = json.parse(languagesStr);
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
		_entries: entries,
		_ucr: ucr,
		_availableLocales: availableLocales,
		_localeLang: kernel.locale.split('-')[0],
		_localeWithUnderscore: kernel.locale.replace('-', '_'),

		// matching data-i18n attribute in HTML code
		_translations: {
			header: _('UCS - {hostname}.{domainname}', ucr),
			claim: _('Welcome to Univention Corporate Server <b>{hostname}.{domainname}</b>', ucr),
			services: _('Installed web services'),
			admin: _('Administration'),
			noServiceTitle: _('There are currently no user web services installed.'),
			noServiceDescription: _('Additional services may be installed in the category <a href="#admin">Administration</a> via Univention Management Console.'),
			wiki: _('Univention Wiki'),
			forum: _('Univention Forum'),
			sdb: _('Univention Support Database'),
			manual: _('Manual for Univention Corporate Server'),
			apps: _('App Catalogue'),
			products: _('Additional Products'),
			solutions: _('Solutions based on UCS'),
			univention_website: _('Univention Website'),
			news: _('News'),
			dates: _('Dates'),
			univention_partner: _('Univention Partners'),
			'http://wiki.univention.de/': _('http://wiki.univention.de/'),
			'http://forum.univention.de/': _('http://forum.univention.de/'),
			'http://sdb.univention.de/': _('http://sdb.univention.de/'),
			'http://docs.univention.de/en.html': _('http://docs.univention.de/en.html'),
			'http://www.univention.de/en/products/ucs/app-catalogue/': _('http://www.univention.de/en/products/ucs/app-catalogue/'),
			'http://www.univention.de/en/products/': _('http://www.univention.de/en/products/'),
			'http://www.univention.de/en/ucs-solutions/': _('http://www.univention.de/en/ucs-solutions/'),
			'http://www.univention.de/en/': _('http://www.univention.de/en/'),
			'http://www.univention.de/en/univention/news/news-releases/': _('http://www.univention.de/en/univention/news/news-releases/'),
			'http://www.univention.de/en/univention/dates/': _('http://www.univention.de/en/univention/dates/'),
			'http://www.univention.de/en/partner/': _('http://www.univention.de/en/partner/')
		},

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

		_getLinkEntry: function(props) {
			var localizedProps = {};
			array.forEach(['link', 'icon', 'label', 'description'], lang.hitch(this, function(ikey) {
				localizedProps[ikey] = this._localizeString(props[ikey]);
			}));
			var node = domConstruct.toDom(lang.replace(
				'<li class="item col-md-6">\n'
				+ '	<a href="{link}">\n'
				+ '		<span class="wrapper">\n'
				+ '			<span class="icon" style="background-image:url({icon})"></span>\n'
				+ '			<span class="title">{label}</span>\n'
				+ '			<span class="text">{description}</span>\n'
				+ '		</span>\n'
				+ '	</a>\n'
				+ '</li>\n',
				localizedProps
			));
			return node;
		},

		_getLinkEntries: function(category) {
			if (!this._entries[category]) {
				return [];
			}
			return array.map(this._entries[category], lang.hitch(this, function(ientry) {
				return this._getLinkEntry(ientry);
			}));
		},

		_placeLinkEntriesInDom: function(category) {
			var listNode = query(lang.replace('#{0} .items', [category]))[0];
			array.forEach(this._getLinkEntries(category), lang.hitch(this, function(ientryNode) {
				domConstruct.place(ientryNode, listNode);
			}));
		},

		_focusTab: function(category) {
			// bootstrap specific command tab()...
			$(lang.replace('#site-header .nav-tabs a[href=#{0}]', [category])).tab('show');
		},

		_focusAdminTab: function() {
			if (!this._entries.service.length) {
				this._focusTab('admin');
			}
		},

		_updateActiveTab: function() {
			var hash = window.location.hash;
			if (!hash || hash == '#') {
				return;
			}
			var activeNode = query(lang.replace('#site-header .nav-tabs a[href={0}]', [hash]));
			var nodeExists = activeNode.length > 0;
			if (!nodeExists) {
				return;
			}
			var category = hash.replace('#', '');
			this._focusTab(category);
		},

		_updateNoServiceHint: function() {
			domStyle.set('no-service', 'display', this._entries.service.length ? 'none' : 'block');
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

		_updateAvailableLocales: function() {
			queryParams = window.location.search.substring(1, window.location.search.length);
			queryObject = ioQuery.queryToObject(queryParams);
			var menuNode = query('#header-right #language-switcher')[0];
			array.forEach(this._availableLocales, function(ilocale) {
				queryObject.lang = ilocale.id;
				domConstruct.place(lang.replace('<li role="presentation"><a role="menuitem" tabindex="-1" href="?{0}">{1}</a></li>', [ioQuery.objectToQuery(queryObject), ilocale.label]), menuNode);
			});
		},

		_updateLocales: function() {
			this._updateCurrentLocale();
			this._updateAvailableLocales();
		},

		_updateTranslations: function() {
			query('*[data-i18n]').forEach(lang.hitch(this, function(inode) {
				var value = domAttr.get(inode, 'data-i18n');
				if (value in this._translations) {
					domAttr.set(inode, 'innerHTML', this._translations[value]);
				}
			}));
			query('a[href]').forEach(lang.hitch(this, function(inode) {
				var href = domAttr.get(inode, 'href');
				if (href in this._translations) {
					domAttr.set(inode, 'href', this._translations[href]);
				}
			}));
		},

		_registerHashChangeEvent: function() {
			on(window, 'hashchange', lang.hitch(this, '_updateActiveTab'));
		},

		start: function() {
			this._updateNoScriptElements();
			this._updateLinkEntries();
			this._updateLocales();
			this._updateTranslations();
			this._registerHashChangeEvent();
			this._updateActiveTab();
		}
	};
});

