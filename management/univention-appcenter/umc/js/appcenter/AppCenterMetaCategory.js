/*
 * Copyright 2013-2019 Univention GmbH
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
/*global define require */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/on",
	"dojo/has",
	"dojo/query",
	"dojo/dom-class",
	"dojo/dom-style",
	"dojo/dom-geometry",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/modules/appcenter/AppCenterGallery",
	"umc/widgets/ContainerWidget",
	"umc/i18n!"
], function(declare, lang, array, win, on, has, domQuery, domClass, domStyle, domGeom, Memory, Observable, tools, Text, Button, AppCenterGallery, Container, _) {
	return declare("umc.modules.appcenter.AppCenterMetaCategory", [Container], {
		// summary:
		//		Offers a container which contains a label, More/Less button and a grid to
		//		display a meta category.
		//		This class is used on the AppCenterPage.

		label: null, // content as string
		_label: null, // Text widget

		button: null,
		_visibilityDeferred: null, // for updaeting the visibility of the button

		grid: null,

		query: null, // query for setting the store
		filterQuery: null, // query to filter the store

		store: null,

		allAppsDisplayed: true, // false: only one row of apps is shown

		baseClass: 'appcenterMetaCategory',

		galleryClass: AppCenterGallery,

		// For tracking of interaction with the "Suggestions based on installed apps" category
		isSuggestionCategory: false,

		buildRendering: function() {
			this.inherited(arguments);

			this._label = new Text({
				content: this.label
			});

			this.button = new Button({
				label: _('More'),
				onClick: lang.hitch(this, function() {
					if (this.button.label === _('More')) {
						this.showAllApps();
					} else {
						this.showOneRowOfApps();
					}
				})
			});

			var clearContainer = new Container({
				style: {
					clear: 'both'
				}
			});

			this.grid = new this.galleryClass({
				actions: [{
					name: 'open',
					isDefaultAction: true,
					isContextAction: false,
					label: _('Open'),
					callback: lang.hitch(this, function(id, app) {
						// for touch devices like smartphones and tablets:
						// on the first touch show hover with long desc
						// on second touch open app
						if (has('touch')) {
							var appNode = domQuery(lang.replace('[moduleid="{id}"]', app), this.grid.contentNode)[0];
							var isSecondTouch = domClass.contains(appNode, 'secondTouch');
							if (isSecondTouch) {
								this.onShowApp(app, this.isSuggestionCategory);
							} else {
								domClass.add(appNode, 'hover secondTouch');
							}
						} else {
							this.onShowApp(app, this.isSuggestionCategory);
						}
					})
				}],
				queryOptions: {sort: tools.cmpObjects({
						attribute: 'name',
						ignoreCase: true
					})},
				store: new Observable(new Memory())
			});

			this.addChild(this._label);
			this.own(this._label);
			//this.addChild(this.button);
			//this.own(this.button);
			this.addChild(clearContainer);
			this.own(clearContainer);
			this.addChild(this.grid);
			this.own(this.grid);

			this.own(on(win.global, 'resize', lang.hitch(this, function() {
				this._handleResize();
			})));
		},

		showAllApps: function() {
			domClass.add(this.grid.domNode, 'open');
			this.button.set('label', _('Less'));
			this.set('allAppsDisplayed', true);
		},

		showOneRowOfApps: function() {
			domClass.remove(this.grid.domNode, 'open');
			this.button.set('label', _('More'));
			this.set('allAppsDisplayed', false);
		},

		_setStoreAttr: function(applications) {
			var filteredApps = array.filter(applications, this.query);
			var store = this.grid.get('store');
			array.forEach(filteredApps, function(app) {
				if (store.get(app.id)) {
					store.put(app);
				} else {
					store.add(app);
				}
			});
			store.query().forEach(function(app) {
				if (! array.some(filteredApps, function(filteredApp) { return filteredApp.id == app.id; })) {
					store.remove(app.id);
				}
			});
			tools.defer(lang.hitch(this, '_centerApps'), 100);
			this._set('store', filteredApps);
		},

		_setFilterQueryAttr: function(query) {
			this.grid.set('query', query);
			this._set('filterQuery', query);
			this._updateVisibility();
		},

		_handleResize: function() {
			if (!this._visibilityDeferred || this._visibilityDeferred.isFulfilled()) {
				this._visibilityDeferred = tools.defer(lang.hitch(this, '_centerApps'), 100);
			}
		},

		_updateButtonVisibility: function() {
			//make sure the domNode is not hidden
			domClass.remove(this.domNode, 'dijitDisplayNone');
			var appsDisplayed = domQuery('div[class*="dgrid-row"]', this.id);
			if (appsDisplayed.length) {
				var gridMarginBox = domGeom.getMarginBox(this.grid.domNode);
				var gridWidth = gridMarginBox.w;
				var appDomNode = appsDisplayed[0];
				var appMarginBox = domGeom.getMarginBox(appDomNode);
				var appWidth = appMarginBox.w;
				var neededWidthToDisplayApps = appsDisplayed.length * appWidth;


				var hideButton = neededWidthToDisplayApps < gridWidth;
				domClass.toggle(this.button.domNode, 'hiddenButton', hideButton);
			}
			this._updateVisibility(appsDisplayed);
		},

		_centerApps: function() {
			this.grid._resizeItemNames();
			//make sure the domNode is not hidden
			domClass.remove(this.domNode, 'dijitDisplayNone');
			var appsDisplayed = domQuery('div[class*="dgrid-row"]', this.id);
			var gridContentNodes = domQuery('div[class="dgrid-content ui-widget-content"]', this.id);
			if (appsDisplayed.length && gridContentNodes.length) {
				var gridContentNode = gridContentNodes[0];
				var gridContentWidth = domGeom.getMarginBox(gridContentNode).w;
				var appDomNode = appsDisplayed[0];
				var appWidth = domGeom.getMarginBox(appDomNode).w;
				var leftMargin = (gridContentWidth % appWidth) / 2;
				domStyle.set(gridContentNode, "margin-left", leftMargin + "px");
			}
			this._updateVisibility(appsDisplayed);
		},

		_updateVisibility: function(apps) {
			var appsDisplayed = apps || domQuery('div[class*="dgrid-row"]', this.id);
			var isMetaCategoryEmpty = appsDisplayed.length === 0;
			domClass.toggle(this.domNode, 'dijitDisplayNone', isMetaCategoryEmpty);
		},

		onShowApp: function(app, fromSuggestionCategory) {
		}
	});
});
