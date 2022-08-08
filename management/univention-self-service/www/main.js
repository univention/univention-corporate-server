/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2015-2022 Univention GmbH
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
/*global define,require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/hash",
	"dojo/io-query",
	"dojo/topic",
	"dojo/dom",
	"dojo/Deferred",
	"dojox/widget/Standby",
	"dijit/layout/StackContainer",
	"dijit/layout/ContentPane",
	"umc/tools",
	"umc/widgets/StandbyMixin",
	"put-selector/put",
	"./PasswordForgotten",
	"./ProtectAccountAccess",
	"./CreateAccount",
	"./VerifyAccount",
	"./NewPassword",
	"./PasswordChange",
	"./UserAttributes",
	"./PageNotFound"
], function(declare, lang, array, baseWin, dojoHash, ioQuery, topic, dom, Deferred, Standby, StackContainer, ContentPane, tools, StandbyMixin, put, PasswordForgotten, ProtectAccountAccess, CreateAccount, VerifyAccount, NewPassword, PasswordChange, UserAttributes, PageNotFound) {
	var _Container = declare([StackContainer, StandbyMixin]);
	return {
		content_container: null,
		_pagePanes: {},

		/**
		 * Builds the active subpages of the
		 * Password Service.
		 */
		start: function() {
			this._initContainer();
			this._subscribeOnHashEvents();
			this._addSubPages(this._getEnabledPages().concat(PageNotFound));
		},

		_getEnabledPages: function() {
			var pages = [PasswordForgotten, ProtectAccountAccess, CreateAccount, VerifyAccount, NewPassword, PasswordChange, UserAttributes];
			var enabledKeys = pages.filter(function(page) {
				return page.enabledViaUcr;
			}).map(function(page) {
				return page.enabledViaUcr;
			});

			var enabled = {};
			enabledKeys.forEach(function(key) {
				enabled[key] = tools.isTrue(tools.status(key));
			});

			var enabledPages = pages.filter(function(page) {
				return page.enabledViaUcr ? enabled[page.enabledViaUcr] : true;
			});

			return enabledPages;
		},

		_subscribeOnHashEvents: function() {
			topic.subscribe("/dojo/hashchange", lang.hitch(this, function(changedHash) {
				this._loadSubpage(changedHash);
			}));
		},

		_initContainer : function() {
			this.content_container = new _Container({
				"class" : "PasswordServiceContent umcCard2",
				id: "contentContainer",
				doLayout: false
			});
			this.content_container.startup();
			this.content_container.placeAt('content');
		},

		/**
		 * Adds the subpages by name to the Password Service.
		 * */
		_addSubPages: function(pages) {
			array.forEach(pages, lang.hitch(this, function(page){
				page.standby = lang.hitch(this.content_container, 'standby');
				page.standbyDuring = lang.hitch(this.content_container, 'standbyDuring');
				var content = page.getContent();

				// insert navigation bar before first child of the returned page content
				var navHeader = put(content.firstChild, '- div.umcHeaderPage');
				array.forEach(pages, function(ipage){
					if (!ipage.visible) {
						return;
					}
					if (ipage.hash === page.hash) {
						put(navHeader, 'span', ipage.getTitle());
					} else {
						put(navHeader, 'a[href=$]', '#page=' + ipage.hash, ipage.getTitle());
					}
				}, this);

				// create page object
				var pagePane = new ContentPane({
					"class": "PasswordServiceContentChild",
					content: content,
					$page: page
				});
				this._pagePanes[page.hash] = pagePane;
				this.content_container.addChild(pagePane);
			}));
			this._loadSubpage(dojoHash());
		},

		_loadSubpage: function(changedHash) {
			var hash = ioQuery.queryToObject(changedHash).page;
			if (!hash) {
				var enabledPages = this._getEnabledPages();
				var fallbackPage = enabledPages.find(function(page) {
					return page.hash === PasswordForgotten.hash;
				});
				if (!fallbackPage) {
					fallbackPage = enabledPages.find(function(page) {
						return page.visible;
					});
				}
				hash = fallbackPage ? fallbackPage.hash : 'pagenotfound';
				dojoHash(ioQuery.objectToQuery({page: hash}));
				return;
			}
			var isValidPage = this._pagePanes.hasOwnProperty(hash);
			if (!isValidPage) {
				hash = "pagenotfound";
			}

			var pagePane = this._pagePanes[hash];
			this.content_container.selectChild(pagePane);
			pagePane.$page.startup();
		}
    };
});
