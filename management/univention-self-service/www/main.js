/*
 * Copyright 2015-2019 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/hash",
	"dojo/io-query",
	"dojo/topic",
	"dojo/dom",
	"dojox/widget/Standby",
	"dijit/layout/StackContainer",
	"dijit/layout/ContentPane",
	"umc/tools",
	"put-selector/put",
	"./PasswordForgotten",
	"./ProtectAccountAccess",
	"./NewPassword",
	"./PasswordChange",
	"./UserAttributes"
], function(lang, array, baseWin, hash, ioQuery, topic, dom, Standby, StackContainer, ContentPane, tools, put, PasswordForgotten, ProtectAccountAccess, NewPassword, PasswordChange, UserAttributes) {
	return {
		content_container: null,
		backend_info: null,
		subpages: {
			"password_forgotten": PasswordForgotten,
			"protect_account_access": ProtectAccountAccess,
			"new_password": NewPassword,
			"password_change": PasswordChange,
			"user_attributes": UserAttributes
		},
		site_hashes: {},

		_standby: null,

		/**
		 * Builds the active subpages of the
		 * Password Service.
		 */
		start: function() {
			this._initContainer();
			this._subscribeOnHashEvents();
			this._addSubPages(Object.keys(this.subpages));
		},

		_subscribeOnHashEvents: function() {
			topic.subscribe("/dojo/hashchange", lang.hitch(this, function(changedHash) {
				this._loadSubpage(changedHash);
			}));
		},

		_initContainer : function() {
			this.content_container = new StackContainer({
				"class" : "PasswordServiceContent umcCard",
				id: "contentContainer",
				doLayout: false
			});
			this.content_container.startup();

			this._standby = new Standby({
				target: this.content_container.domNode,
				image: require.toUrl("dijit/themes/umc/images/standbyAnimation.svg").toString(),
				duration: 200
			});
			this._standby.placeAt(baseWin.body());
			this.content_container.placeAt('content');
		},

		/**
		 * Adds the subpages by name to the Password Service.
		 * */
		_addSubPages: function(page_list) {
			array.forEach(page_list, lang.hitch(this, function(page_name){
				if (page_name === 'user_attributes' && tools.isFalse(tools.status('umc/self-service/profiledata/enabled'))) {
					return;
				}
				var module = this.subpages[page_name];
				if (module) {
					module.standby = this._standby;
					var content = module.getContent();

					// insert navigation bar before first child of the returned page content
					var navHeader = put(content.firstChild, '- div.umcHeaderPage');
					array.forEach(page_list, function(ipage){
						if (ipage === 'user_attributes' && tools.isFalse(tools.status('umc/self-service/profiledata/enabled'))) {
							return;
						}
						var imodule = this.subpages[ipage];
						if (!imodule || ipage === 'new_password') {
							return;
						}
						if  (ipage === page_name) {
							put(navHeader, 'span', imodule.getTitle());
						} else {
							put(navHeader, 'a[href=$]', '#' + imodule.hash, imodule.getTitle());
						}
					}, this);

					// create page object
					var subpage = new ContentPane({
						"class": "PasswordServiceContentChild",
						content: content,
						page_name: page_name
					});
					this.site_hashes[module.hash] = subpage;
					this.content_container.addChild(subpage);
				}
			}));
			this._loadSubpage(hash());
		},

		_loadSubpage: function(changedHash) {
			var page = ioQuery.queryToObject(changedHash).page;
			if (!page) {
				// Old style hash (prior 4.2)
				page = changedHash;
			}
			var isValidPage = array.some(Object.keys(this.site_hashes), function(site_hash) {
				return site_hash === page;
			});
			if (!isValidPage) {
				hash(ioQuery.objectToQuery({page: "passwordreset"}));
				return;
			}
			var subpage = this.site_hashes[page];
			if (!subpage) {
				subpage = this.content_container.getChildren()[0];
			}
			var page_name = this.site_hashes[page].page_name;
			var module = this.subpages[page_name];
			this.content_container.selectChild(subpage);
			module.startup();
		}
    };
});
