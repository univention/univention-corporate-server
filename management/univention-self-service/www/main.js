/*
 * Copyright 2015-2016 Univention GmbH
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
/*global define*/

define([
	"dojo/hash",
	"dojo/topic",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/xhr",
	"dojo/json",
	"put-selector/put",
	"dojo/dom",
	"dijit/layout/StackContainer",
	"dijit/layout/ContentPane",
	"./PasswordChange",
	"./PasswordForgotten",
	"./ProtectAccountAccess",
	"./NewPassword",
	"./lib",
], function(hash, topic, lang, array, xhr, JSON, put, dom, StackContainer, ContentPane, PasswordChange, PasswordForgotten, ProtectAccountAccess, NewPassword, lib){
	return {
		content_container: null,
		content_controller: null,
		backend_info: null,
		subpages: {
			"password_change": PasswordChange,
			"password_forgotten": PasswordForgotten,
			"protect_account_access": ProtectAccountAccess,
			"new_password": NewPassword
		},
		site_hashes: {},

		/**
		 * Builds the active subpages of the
		 * Password Service.
		 */
		start: function() {
			this._initContainer();
			this._initController();
			this._subscribeOnHashEvents();
			this._addSubPages(["password_forgotten", "protect_account_access", "new_password"]);
		},

		_subscribeOnHashEvents: function() {
			topic.subscribe("/dojo/hashchange", lang.hitch(this, function(changedHash) {
				//window.location.reload();
				lib._removeMessage();
				this._loadSubpage(changedHash);
			}));
		},

		_initContainer : function() {
			this.content_container = new StackContainer({
				"class" : "PasswordServiceContent",
				id: "contentContainer",
				doLayout: false
			}, "content");
			this.content_container.startup();
		},

		_initController: function() {
			var navContainer = dom.byId('navigation');
			this.content_controller = put(navContainer, ".PasswordServiceController");
		},

		/**
		 * Adds the subpages by name to the Password Service.
		 * */
		_addSubPages: function(page_list) {
			array.forEach(page_list, lang.hitch(this, function(page_name){
				var module = this.subpages[page_name];
				if (module) {
					var subpage = new ContentPane({
						content: module.getContent(),
						page_name: page_name
					});
					this.site_hashes[module.hash] = subpage;
					this.content_container.addChild(subpage);
				}
			}));
			this._loadSubpage(hash());
		},

		_loadSubpage: function(changedHash) {
			var hashWithoutQuery = changedHash.split('?', 1)[0];
			var subpage = this.site_hashes[hashWithoutQuery];
			if (!subpage) {
				subpage = this.content_container.getChildren()[0];
			}
			var page_name = this.site_hashes[hashWithoutQuery].page_name;
			var module = this.subpages[page_name];
			this.content_container.selectChild(subpage);
			module.startup();
		}
    };
});
