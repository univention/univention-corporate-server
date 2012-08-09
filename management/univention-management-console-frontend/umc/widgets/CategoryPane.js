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
/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.CategoryPane");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit._Contained");
dojo.require("dijit._Container");
dojo.require("dijit.TitlePane");
dojo.require("tools");
dojo.require("umc.widgets.Tooltip");

//TODO: don't use float, use display:inline-block; we need a hack for IE7 here, see:
//      http://robertnyman.com/2010/02/24/css-display-inline-block-why-it-rocks-and-why-it-sucks/
/*REQUIRE:"dojo/_base/declare"*/ /*TODO*/return declare([dijit.layout.ContentPane, dijit._Contained], {
	modID: '',
	modIcon: '',
	label: '',
	description: '',

	// the widget's class name as CSS class
	'class': 'umcCategoryItem',

	postMixInProperties: function() {
		this.inherited(arguments);
		/*REQUIRE:"dojo/_base/lang"*/ lang.mixin(this, {
			baseClass: 'modLaunchButton',
			'class': tools.getIconClass(this.modIcon, 50),
			content: '<div>' + this.label + '</div>'
		});
	},

	postCreate: function() {
		this.inherited(arguments);

		// add a tooltip
		var tooltip = new umc.widgets.Tooltip({
			label: this.description,
			connectId: [ this.domNode ]
		});

		//this.domNode.innerHtml = '<div>' + this.description + '</div>';
		/*REQUIRE:"dojo/on"*/ /*TODO*/ this.own(this.on(this, 'onMouseOver', function(evt) {
			/*REQUIRE:"dojo/dom-class"*/ domClass.add(this.domNode, 'modLaunchButtonHover');
		});
		/*REQUIRE:"dojo/on"*/ /*TODO*/ this.own(this.on(this, 'onMouseOut', function(evt) {
			/*REQUIRE:"dojo/dom-class"*/ domClass.remove(this.domNode, 'modLaunchButtonHover');
		});
		/*REQUIRE:"dojo/on"*/ /*TODO*/ this.own(this.on(this, 'onMouseDown', function(evt) {
			/*REQUIRE:"dojo/dom-class"*/ domClass.add(this.domNode, 'modLaunchButtonClick');
		});
		/*REQUIRE:"dojo/on"*/ /*TODO*/ this.own(this.on(this, 'onMouseUp', function(evt) {
			/*REQUIRE:"dojo/dom-class"*/ domClass.remove(this.domNode, 'modLaunchButtonClick');
		});
	}
});

/*REQUIRE:"dojo/_base/declare"*/ /*TODO*/return declare([dijit.TitlePane, dijit._Container], {
	// summary:
	//		Widget that displays an overview of all modules belonging to a 
	//		given category along with their icon and description.

	// modules: Array
	//		Array of modules in the format {id:'...', title:'...', description:'...'}
	modules: [],

	// title: String
	//		Title of category for which the modules shall be displayed
	title: '',

	// the widget's class name as CSS class
	'class': 'umcCategoryPane',

	postMixInProperties: function() {
		this.inherited(arguments);
	},

	buildRendering: function() {
		// summary:
		//		Render a list of module items for the given category.

		this.inherited(arguments);

		// iterate over all modules
		/*REQUIRE:"dojo/_base/array"*/ array.forEach(this.modules, /*REQUIRE:"dojo/_base/lang"*/ lang.hitch(this, function(imod) {
			// create a new button widget for each module
			var modWidget = new umc.widgets._CategoryItem({
				modID: imod.id,
				modIcon: imod.icon,
				label: imod.name,
				description: imod.description
			});

			// hook to the onClick event of the module
			/*REQUIRE:"dojo/on"*/ /*TODO*/ this.own(this.on(modWidget, 'onClick', function(evt) {
				this.onOpenModule(imod);
			});

			// add module widget to the container
			this.addChild(modWidget);
		}));

		// we need to add a <br> at the end, otherwise we will get problems 
		// with the visualizaton
		//this.containerNode.appendChild(/*REQUIRE:"dojo/dom-construct"*/ construct.create('br', { clear: 'all' }));
	},

	onOpenModule: function(imod) {
		// event stub
	}
});


