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
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/modules/appcenter/AppCenterGallery",
	"umc/widgets/ContainerWidget",
	"umc/i18n!"
], function(declare, lang, array, domStyle, domClass, Memory, Observable, Text, Button, AppCenterGallery, Container, _) {
	return declare("umc.modules.appcenter.AppCenterMetaCategory", [Container], {
		// summary:
		//		Offers a container which contains a label, More/Less button and a grid to
		//		display a meta category.
		//		This class is used on the AppCenterPage.

		label: null, // content as string
		_label: null, // Text widget

		button: null,

		grid: null,

		query: null,

		baseClass: 'appcenterMetaCategory',

		buildRendering: function() {
			this.inherited(arguments);

			this._label = new Text({
				content: this.label
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
						this.onShowApp(app);
					})
				}],
				style: {
					height: '175px'
				}
			});

			this.button = new Button({
				label: _('More'),
				onClick: lang.hitch(this, function() {
					if (this.label === _('More')) {
						domStyle.set(this.grid.domNode, 'height', 'auto');
						this.set('label', _('Less'));
					} else {
						domStyle.set(this.grid.domNode, 'height', '175px');
						this.set('label', _('More'));
					}
				})
			});

			this.addChild(this._label);
			this.own(this._label);
			this.addChild(this.button);
			this.own(this.button);
			this.addChild(clearContainer);
			this.own(clearContainer);
			this.addChild(this.grid);
			this.own(this.grid);
		},

		postCreate: function() {
			this.inherited(arguments);
		},

		_setStoreAttr: function(applications) {
			var filteredApps = array.filter(applications, this.query);
			this.grid.set('store', new Observable(new Memory({
				data: filteredApps
			})));
			this._set('store', applications);
		},

		_setQueryAttr: function(query) {
			if (this.grid.store) {
				this.grid.set('query', query);
				var queryResult = this.grid.store.query(query);
				domClass.toggle(this.domNode, 'dijitHidden', !queryResult.length);
				this._set('query', query);
			}
		},

		onShowApp: function(app) {
		}
	});
});
