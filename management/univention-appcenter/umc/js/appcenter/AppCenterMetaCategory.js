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
/*global define require console */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/on",
	"dojo/has",
	"dojo/query",
	"dojo/dom",
	"dojo/dom-class",
	"dojo/dom-geometry",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/modules/appcenter/AppCenterGallery",
	"umc/widgets/ContainerWidget",
	"umc/i18n!"
], function(declare, lang, array, win, on, has, domQuery, dom, domClass, domGeom, Memory, Observable, tools, Text, Button, AppCenterGallery, Container, _) {
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

			this.grid = new AppCenterGallery({
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
							var appNode = dom.byId(app.id);
							var isSecondTouch = domClass.contains(appNode, 'secondTouch');
							if (isSecondTouch) {
								this.onShowApp(app);
							} else {
								domClass.add(appNode, 'hover secondTouch');
							}
						
						} else {
							this.onShowApp(app);
						}
					})
				}]
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
				this._handleButtonVisibility();
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
			this.grid.set('store', new Observable(new Memory({
				data: filteredApps
			})));
			this._set('store', applications);
			this._handleButtonVisibility();
		},

		_setFilterQueryAttr: function(query) {
			this.grid.set('query', query);
			this._set('filterQuery', query);
			this._handleButtonVisibility();
		},

		_handleButtonVisibility: function() {
			if (!this._visibilityDeferred || this._visibilityDeferred.isFulfilled()) {
				this._visibilityDeferred = tools.defer(lang.hitch(this, '_updateButtonVisibility'), 200);
			}
		},

		_updateButtonVisibility: function() {
			//make sure the domNode is not hidden
			domClass.remove(this.domNode, 'dijitHidden');
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
			domClass.toggle(this.domNode, 'dijitHidden', !appsDisplayed.length);
		},

		onShowApp: function(app) {
		}
	});
});
