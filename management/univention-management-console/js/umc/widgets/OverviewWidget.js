/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.OverviewWidget");

dojo.require("dijit.layout.ContentPane");
dojo.require("dijit._Contained");
dojo.require("dijit._Container");
dojo.require("dijit.TitlePane");

dojo.declare( "umc.widgets._OverviewItemWidget", [dijit.layout.ContentPane, dijit._Contained], {
	modID: '',
	description: '',

	postMixInProperties: function() {
		this.inherited(arguments);
		dojo.mixin(this, {
			baseClass: 'modLaunchButton',
			'class': 'icon64-' + this.modID,
			content: '<div>' + this.description + '</div>'
		});
	},

	postCreate: function() {
		this.inherited(arguments);

		//this.domNode.innerHtml = '<div>' + this.description + '</div>';
		dojo.connect(this, 'onMouseOver', dojo.hitch(this, function(evt) {
			dojo.addClass(this.domNode, 'modLaunchButtonHover');
		}));
		dojo.connect(this, 'onMouseOut', dojo.hitch(this, function(evt) {
			dojo.removeClass(this.domNode, 'modLaunchButtonHover');
		}));
		dojo.connect(this, 'onMouseDown', dojo.hitch(this, function(evt) {
			dojo.addClass(this.domNode, 'modLaunchButtonClick');
		}));
		dojo.connect(this, 'onMouseUp', dojo.hitch(this, function(evt) {
			dojo.removeClass(this.domNode, 'modLaunchButtonClick');
		}));
	}
});

dojo.declare( "umc.widgets.OverviewWidget", [dijit.TitlePane, dijit._Container], {
	// summary:
	//		Widget that displays an overview of all modules belonging to a 
	//		given category along with their icon and description.

	// modules: Array
	//		Array of modules in the format {id:'...', title:'...', description:'...'}
	modules: [],

	// title: String
	//		Title of category for which the modules shall be displayed
	title: '',

	postMixInProperties: function() {
		this.inherited(arguments);
	},
	
	buildRendering: function() {
		// summary:
		//		Render a list of module items for the given category.

		this.inherited(arguments);

		// iterate over all modules
		dojo.forEach(this.modules, dojo.hitch(this, function(imod) {
			// create a new button widget for each module
			var modWidget = new umc.widgets._OverviewItemWidget({
				modID: imod.id,
				description: imod.title
			});

			// hook to the onClick event of the module
			dojo.connect(modWidget, 'onClick', dojo.hitch(this, function(evt) {
				this.onOpenModule(imod.id);
			}));

			// add module widget to the container
			this.addChild(modWidget);
		}));
		
		// we need to add a <br> at the end, otherwise we will get problems 
		// with the visualizaton
		this.containerNode.appendChild(dojo.create('br', { clear: 'all' }));
	},

	onOpenModule: function(imod) {
		// event stub
	}
});


