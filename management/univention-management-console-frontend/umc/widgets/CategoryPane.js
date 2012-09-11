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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/mouse",
	"dojo/dom-class",
	"dijit/layout/ContentPane",
	"dijit/_Container",
	"dijit/_Contained",
	"dijit/TitlePane",
	"umc/tools",
	"umc/widgets/Tooltip"
], function(declare, lang, array, on, mouse, domClass, ContentPane, _Container, _Contained, TitlePane, tools, Tooltip) {
	//TODO: don't use float, use display:inline-block; we need a hack for IE7 here, see:
	//      http://robertnyman.com/2010/02/24/css-display-inline-block-why-it-rocks-and-why-it-sucks/a
	var _CategoryItem = declare("umc.widgets._CategoryItem", [ContentPane, _Contained], {
		modID: '',
		modIcon: '',
		label: '',
		categories: null,
		description: '',
		_tooltip: null,

		// the widget's class name as CSS class
		'class': 'umcCategoryItem',

		postMixInProperties: function() {
			this.inherited(arguments);
			var content = '<div>' + this.label + '</div>'
			if (this.categories && this.categories.length) {
				content += '<div style="color: grey; margin-top: 0;">' + this.categories.join(', ') + '</div>';
			}
			lang.mixin(this, {
				baseClass: 'modLaunchButton',
				'class': tools.getIconClass(this.modIcon, 50),
				content: content
			});
		},

		postCreate: function() {
			this.inherited(arguments);

			// add a tooltip
			this._tooltip = new Tooltip({
				label: this.description,
				connectId: [ this.domNode ]
			});

			//this.domNode.innerHtml = '<div>' + this.description + '</div>';
			var domNode = this.domNode;
			this.on(mouse.enter, function() {
				domClass.add(domNode, 'modLaunchButtonHover');
			});
			this.on(mouse.leave, function() {
				domClass.remove(domNode, 'modLaunchButtonHover');
			});
			this.on('mousedown', function() {
				domClass.add(domNode, 'modLaunchButtonClick');
			});
			this.on('mouseup', function() {
				domClass.remove(domNode, 'modLaunchButtonClick');
			});
		}
	});

	return declare("umc.widgets.CategoryPane", [TitlePane, _Container], {
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

	        // add a grey categories string at the bottom of the items
		useCategories: false,

		postMixInProperties: function() {
			this.inherited(arguments);
		},

		buildRendering: function() {
			// summary:
			//		Render a list of module items for the given category.

			this.inherited(arguments);

			// iterate over all modules
			array.forEach(this.modules, lang.hitch(this, function(imod) {
				// create a new button widget for each module
				obj = {
					modID: imod.id,
					modIcon: imod.icon,
					label: imod.name,
					description: imod.description
				};
				if (this.useCategories) {
					obj.categories = imod.categories;
				}
				var modWidget = new _CategoryItem(obj);

				// hook to the onClick event of the module
				this.own(on(modWidget, 'click', lang.hitch(this, function() {
					this.onOpenModule(imod);
				})));

				// add module widget to the container
				this.addChild(modWidget);
			}));

			// we need to add a <br> at the end, otherwise we will get problems
			// with the visualizaton
			//this.containerNode.appendChild(domConstruct.create('br', { clear: 'all' }));
		},

		onOpenModule: function(imod) {
			// event stub
		}
	});
});

