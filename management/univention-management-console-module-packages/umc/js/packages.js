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
/*global dojo umc */

dojo.provide("umc.modules.packages");

dojo.require("umc.i18n");
dojo.require("umc.modules._packages.store");
//dojo.require("umc.store");

dojo.require("umc.widgets.TabbedModule");
dojo.require("umc.modules._packages.AppCenterPage");
dojo.require("umc.modules._packages.PackagesPage");
dojo.require("umc.modules._packages.ComponentsPage");
dojo.require("umc.modules._packages.DetailsPage");
dojo.require("umc.modules._packages.SettingsPage");

dojo.declare("umc.modules.packages", [ umc.widgets.TabbedModule, umc.i18n.Mixin ], {

	i18nClass: 'umc.modules.packages',
	idProperty: 'package',

	buildRendering: function() {

		pack = this;
		this.inherited(arguments);
		this._componentsStore = umc.modules._packages.store.getModuleStore('name', 'packages/components')

		this._app_center = new umc.modules._packages.AppCenterPage({});
		this._packages = new umc.modules._packages.PackagesPage({moduleStore: this.moduleStore});
		this._components = new umc.modules._packages.ComponentsPage({moduleStore: this._componentsStore});
		this._details = new umc.modules._packages.DetailsPage({moduleStore: this._componentsStore});
		this._settings = new umc.modules._packages.SettingsPage({});

		this.addChild(this._app_center);
		this.addChild(this._packages);
		this.addChild(this._components);
		this.addChild(this._details);
		this.addChild(this._settings);

		// switches from 'add' or 'edit' (components grid) to the detail form
		dojo.connect(this._components, 'showDetail', dojo.hitch(this, function(id) {
			this.exchangeChild(this._components, this._details);
			if (id) {
				// if an ID is given: pass it to the detail page and let it load
				// the corresponding component record
				this._details.startEdit(false, id);
			} else {
				// if ID is empty: ask the SETTINGS module for default values.
				this._details.startEdit(true, this._details.getComponentDefaults());
			}
		}));

		// closes detail form and returns to grid view.
		dojo.connect(this._details, 'closeDetail', dojo.hitch(this, function(args) {
			this._details._form.clearFormValues();
			this.exchangeChild(this._details, this._components);
		}));

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

