/*
 * Copyright 2013-2015 Univention GmbH
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
/*global define require console window */

define([
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/io-query",
	"dojo/query",
	"dojo/dom",
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/on",
	"dojo/router",
	"dojo/hash",
	"dijit/Menu",
	"dijit/MenuItem",
	"dijit/form/DropDownButton",
	"dijit/DropDownMenu",
	"dojox/form/Uploader",
	"put-selector/put",
	"./text!/languages.json",
	"./text!/entries.json",
	"./text!/license",
	"./i18n!"
], function(lang, kernel, array, ioQuery, query, dom, domConstruct, domAttr, domStyle, domClass, domGeometry, on, router, hash, Menu, MenuItem, DropDownButton, DropDownMenu, Uploader, put, _availableLocales, entries, license, _) {
	// make sure that en-US exists
	var existsEnUsLocale = array.some(_availableLocales, function(ilocale) {
		return ilocale.id == 'en-US';
	});
	if (!existsEnUsLocale) {
		_availableLocales.push({
			id: 'en-US',
			label: 'English'
		});
	}

	var isTrue = function(input) {
		//('yes', 'true', '1', 'enable', 'enabled', 'on')
		if (typeof input == "string") {
			switch (input.toLowerCase()) {
				case 'yes':
				case 'true':
				case '1':
				case 'enable':
				case 'enabled':
				case 'on':
					return true;
			}
		}
		return false;
	};
	var hasLicense = Boolean(entries.license_uuid);
	var hasLicenseRequested = isTrue(entries.license_requested);
    var showRequestLicenseTab = !hasLicense && !hasLicenseRequested;


	return {
		_availableLocales: _availableLocales,
		_localeLang: kernel.locale.split('-')[0],
		_localeWithUnderscore: kernel.locale.replace('-', '_'),
		_resizeTimeout: null,
		_uploader: null,

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

		registerRouter: function() {
			router.register(":category", lang.hitch(this, function(data){
				this._focusTab(data.params.category);
			}));
		},

		_hasCategoryBar: function() {
			var nodes = query('#category-bar');
			return nodes.length;
		},

		_getTab: function(id) {
			var nodes = query(lang.replace('#{0}-tab', [id]));
			if (!nodes.length) {
				return;
			}
			return nodes[0];
		},

		_getFocusedTab: function() {
			//return this.servicesButton.selected ? 'service-tab' : 'admin-tab';
		},

		_focusTab: function(category) {
			// set visibility of tabs through css and also set 'selectd' of category buttons
			//domClass.toggle("service-tab", "galleryTabInvisible", category != "service");
			//this.servicesButton.set('selected', category == "service");
			//domClass.toggle("admin-tab", "galleryTabInvisible", category == "service");
			//this.adminButton.set('selected', category != "service");
		},

		_getLinkEntry: function(props, category, id) {
			id = id || '';
			var localizedProps = {
				category: category,
				id: id
			};
			array.forEach(['link', 'icon', 'label', 'description'], lang.hitch(this, function(ikey) {
				localizedProps[ikey] = this._localizeString(props[ikey]);
			}));
			if ((props.port_http || props.port_https) && localizedProps.link && localizedProps.link.indexOf('/') === 0) {
				var protocol = window.location.protocol;
				var port = '';
				if (protocol == 'http:') {
					port = props.port_http;
					if (!port) {
						port = props.port_https;
						protocol = 'https:';
					}
				} else if (protocol == 'https:') {
					port = props.port_https;
					if (!port) {
						port = props.port_http;
						protocol = 'http:';
					}
				}
				if (port == '80') {
					protocol = 'http:';
					port = '';
				} else if (port == '443') {
					protocol = 'https:';
					port = '';
				}
				if (port) {
					port = ':' + port;
				}
				localizedProps.link = protocol + '//' + window.location.hostname + port + localizedProps.link;
			}
			var node = domConstruct.toDom(lang.replace(
				'<div class="umcGalleryWrapperItem col-xxs-12 col-xs-6 col-sm-6 col-md-4" id="{id}">\n'
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
			var listNode = this._getTab(category);
			array.forEach(this._getLinkEntries(category), lang.hitch(this, function(ientryNode) {
				domConstruct.place(ientryNode, listNode);
			}));
		},

		_updateNoServiceHint: function() {
			domClass.toggle('no-service', 'dijitHidden', this._hasServiceEntries());
		},

		_getAvailableLocales: function() {
			if ('availableLocales' in window) {
				return availableLocales;
			}
			return this._availableLocales;
		},

		_hasLanguagesDropDown: function() {
			return dom.byId('dropDownButton');
		},

		createLanguagesDropDown: function() {
			if (!this._hasLanguagesDropDown()) {
				return;
			}
			var _languagesMenu = new DropDownMenu({ style: "display: none;"});
			array.forEach(this._getAvailableLocales(), function(ilocale) {
				var newMenuItem = new MenuItem ({
					label: ilocale.label,
					id: ilocale.id,
					onClick: function() {
						if (ilocale.href) {
							// full href link is given... go to this URL
							window.location.href = ilocale.href;
							return;
						}

						// adjust query string parameter and reload page
						var queryObj = {};
						var queryString = window.location.search;
						if (queryString.length) {
							// cut off the '?' character
							queryObj = ioQuery.queryToObject(queryString.substring(1))
						}
						queryKey = ilocale.queryKey || 'lang';
						queryObj[queryKey] = ilocale.id;
						queryString = ioQuery.objectToQuery(queryObj);
						window.location.search = '?' + queryString;
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
			domConstruct.place(_toggleButton.domNode, 'dropDownButton');
		},

		_createTitle: function() {
			var titleNode = dom.byId('title');
			put(titleNode, 'h1', _('Activation of Univention Corporate Server'));
			//put(titleNode, 'h2', _(''));
			put(titleNode, '!.dijitHidden');
		},

		_createUploader: function() {
			// until Dojo2.0 "dojox.form.Uploader" must be used!
			this._uploader = new dojox.form.Uploader({
				url: '/license',
				name: 'license',
				label: _('Upload license file'),
				uploadOnSelect: true,
				getForm: function() {
					// make sure that the Uploader does not find any of our encapsulating forms
					return null;
				}
			});
			put(this._uploader.domNode, '.umcButton[display=inline-block]');
			//this._uploader.set('iconClass', 'umcIconAdd');
			return this._uploader.domNode;
		},

		_createUploadTab: function() {
			var contentNode = dom.byId('content');
			var tabNode = put(contentNode, 'div.tab');
			put(tabNode, 'p > b', _('You have got mail!'));
			put(tabNode, 'p', _('A license file should have been sent to your email address. Upload the license file from the email to activate your UCS instance.'));
			put(tabNode, '>', this._createUploader());
			this._uploader.startup();
		},

		createElements: function() {
			this._createTitle();
			this._createUploadTab();
		},

		start: function() {
			this.registerRouter();
			this.createLanguagesDropDown();
			this.createElements()
			router.startup('welcome');
		}
	};
});

