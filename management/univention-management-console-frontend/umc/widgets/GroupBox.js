/*global dojo dijit dojox umc console */
/*
	Author: Jens Arps, http://jensarps.de/
	Available via Academic Free License >= 2.1 OR the modified BSD license.
	Modifications: Univention GmbH, Bremen, Germany
*/
dojo.provide("umc.widgets.GroupBox");

dojo.require("dijit.TitlePane");
dojo.require("dijit.layout._LayoutWidget");

dojo.declare("umc.widgets.GroupBox", [dijit.TitlePane, dijit.layout._LayoutWidget], {   
	// summary:
	//		A fieldset that can be expanded or collapsed.
	//
	// description:
	//		An accessible fieldset that can be expanded or collapsed via 
	//		it's legend. GroupBox extends `dijit.TitlePane`.
	//
	//
	// example:
	// |	<!-- markup href example: -->
	// |	<div dojoType="umc.widgets.GroupBox" href="foobar.html" legend="The Legend"></div>
	// 
	// example:
	// |	<!-- fieldset markup -->
	// | 	<fieldset dojoType="umc.widgets.GroupBox">
	// |        <legend>The Legend</legend>
	// |		<p>Some content</p>
	// |	</div>
	//
	// example:
	// |	// programmatic
	// |	var fieldset = new umc.widgets.GroupBox({legend:'dojo fieldset 4'}).placeAt(dojo.body());
	// |	fieldset.set('content','<p>I was created programmatically!</p>');
	

	// baseClass: [protected] String
	//		The root className to use for the various states of this widget
    baseClass: 'umcGroupBox',
    
	// legend: String
	//		Content of the legend tag. Overrides <legend> tag, if present in markup.
    legend: '',

    templateString: '',
    templatePath: dojo.moduleUrl("umc.widgets", "templates/GroupBox.html"),
    
    postCreate: function() {
        this.setupLegend();

		this.inherited(arguments);
    },
    
    setupLegend: function() {
		// summary:
		//		Sets up the content of the <legend> tag.
		// 		Will take the legend argument, if given, or search for given legend
		// 		node in markup.
    	
    	// did we receive a legend?
    	if(this.legend !== '') {
            this.set('legend',this.legend);
    	} else { // try and find legend tag
            var legends = dojo.query('legend',this.containerNode),
            	fieldsets = dojo.query('fieldset',this.containerNode);
            if(!legends.length) { // oops, no legend?
                return;
            }
            // copy text
            this.set('legend',legends[0].innerHTML);
            // remove
            if(legends.length == (fieldsets.length + 1)) {
            	legends[0].parentNode.removeChild(legends[0]);
            }
    	}

    },
    
	_handleHover: function(e) {
    	// summary:
    	//		Handle hover states for the legend
    	// tags:
    	//		private
    	
		dojo.toggleClass(this.focusNode, this.baseClass + "Legend-hover", e.type === 'mouseover');
	},
	
	_setLegendAttr: function(/* String */ legend) {
		// summary:
		//		Hook to set the legend via set("legend", legend).
		// legend: String
		//		The text that should umc.widgetsear in the legend.
		
		this.legendTextNode.innerHTML = legend;
	},
	
	_setTitleAttr: function(/* String */ title) {
		// summary:
		//		Alias for set("legend", legend), so that existing TitlePane code
		//		works with this GroupBox.
		// title: String
		//		The text that should umc.widgetsear in the legend.
		
		this.set('legend',title);
	}
}
);
