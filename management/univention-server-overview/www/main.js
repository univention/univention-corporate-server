/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/dom",
	"dojo/dom-class",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"dijit/registry",
	"dojox/html/entities",
	"login",
	"umc/tools",
	"umc/menu",
	"umc/i18n!server-overview"
], function(declare, lang, array, kernel, dom, domClass, Memory, Observable, registry, entities, login, tools, menu, _) {

	return {
		standby: function(standby) {
			if (standby) {
				tools.toggleVisibility(this._standbyNode, true);
				setTimeout(lang.hitch(this, function() {
					domClass.add(this._standbyNode, 'standbyShown');
				}), 0);
			} else {
				domClass.remove(this._standbyNode, 'standbyShown');
				setTimeout(lang.hitch(this, function() {
					tools.toggleVisibility(this._standbyNode, false);
				}), 300); // FIXME hardcoded value for transition duration in css
			}
		},

		start: function() {
			this._standbyNode = dom.byId('standby');
			this.initLabels();
			login.onInitialLogin(lang.hitch(this, 'init'));
		},

		init: function() {
			this.initGallery();
			this.initLiveSearch();
		},

		initLabels: function() {
			var title = entities.encode(_('%s - Server overview', tools.status('domainname')));
			window.document.title = title;

			title = entities.encode(_('Server overview for domain %s', tools.status('domainname')));
			dom.byId('title').innerHTML = title;

			this.liveSearch = registry.byId('liveSearch');
			this.liveSearch.set('searchLabel', _('Search servers'));
			// this.liveSearch._searchTextBox.set('inlineLabel', _('Search servers'));
		},

		initLiveSearch: function() {
			this.liveSearch.on('search', lang.hitch(this, function(pattern) {
				this.gallery.updateQuery(this.liveSearch.get('value'));
			}));
		},

		initGallery: function() {
			var serverPriorities = {
				master: 1,
				backup: 2,
				slave: 3,
				member: 4
			};

			this.gallery = registry.byId('gallery');
			this.gallery.useFqdn = tools.isFQDN(window.location.hostname);
			tools.umcpCommand('serveroverview/query').then(lang.hitch(this, function(response) {
				// create a field _priority for sorting w.r.t. to server type
				var data = response.result;
				array.forEach(data, function(item) {
					if (item.serverRole instanceof Array) {
						item._priority = serverPriorities[item.serverRole[0]];
					}
					if (!item._priority) {
						// fallback
						item._priority = 5;
					}
				});

				// store object
				var store = new Observable(new Memory({
					data: data,
					idProperty: 'dn'
				}));
				this.gallery.set('store', store);

				// sort w.r.t. to server type and hostname
				this.gallery.set('queryOptions', {
					sort: [{
						attribute: '_priority',
						descending: false
					}, {
						attribute: 'hostname',
						descending: false
					}]
				});
				this.standby(false);
			}));
		}
	};
});
