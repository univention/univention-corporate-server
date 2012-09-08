/*
 * Copyright 2011-2012 Univention GmbH
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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/aspect",
	"umc/modules/packages/store",
	"umc/widgets/TabbedModule",
	"umc/modules/packages/AppCenterPage",
	"umc/modules/packages/PackagesPage",
	"umc/modules/packages/ComponentsPage",
	"umc/modules/packages/DetailsPage",
	"umc/modules/packages/SettingsPage",
	"umc/i18n!umc/modules/packages" // not needed atm
], function(declare, lang, aspect, store, TabbedModule, AppCenterPage, PackagesPage, ComponentsPage, DetailsPage, SettingsPage, _) {
	return declare("umc.modules.packages", [ TabbedModule ], {

		idProperty: 'package',

		buildRendering: function() {

			this.inherited(arguments);
			this._componentsStore = store('name', 'packages/components');

			this._app_center = new AppCenterPage({});
			this._packages = new PackagesPage({moduleStore: this.moduleStore});
			this._components = new ComponentsPage({moduleStore: this._componentsStore});
			this._details = new DetailsPage({moduleStore: this._componentsStore});
			this._settings = new SettingsPage({});

			this.addChild(this._app_center);
			this.addChild(this._packages);
			this.addChild(this._components);
			this.addChild(this._details);
			this.addChild(this._settings);

			// switches from 'add' or 'edit' (components grid) to the detail form
			this.own(aspect.after(this._components, 'showDetail', lang.hitch(this, function(id) {
				this.exchangeChild(this._components, this._details);
				if (id) {
					// if an ID is given: pass it to the detail page and let it load
					// the corresponding component record
					this._details.startEdit(false, id);
				} else {
					// if ID is empty: ask the SETTINGS module for default values.
					this._details.startEdit(true, this._details.getComponentDefaults());
				}
			})));

			// closes detail form and returns to grid view.
			this.own(aspect.after(this._details, 'closeDetail', lang.hitch(this, function() {
				this._details._form.clearFormValues();
				this.exchangeChild(this._details, this._components);
			})));

		},

		startup: function() {

			this.inherited(arguments);

			this.hideChild(this._details);

		},

		// FIXME: this is quite cool. should go into TabbedModule
		// exchange two tabs, preserve selectedness.
		exchangeChild: function(from,to) {
			var what = 'nothing';
			try
			{
				what = 'getting FROM selection';
				var is_selected = from.get('selected');
				what = 'hiding FROM';
				this.hideChild(from);
				what = 'showing TO';
				this.showChild(to);
				if (is_selected)
				{
					what = 'selecting TO';
					this.selectChild(to);
				}
			}
			catch(error)
			{
				console.error("exchangeChild: [" + what + "] " + error.message);
			}
		}

		// TODO hideChild() should check selectedness too, and
		// select a different tab when needed.
			
	});
});

