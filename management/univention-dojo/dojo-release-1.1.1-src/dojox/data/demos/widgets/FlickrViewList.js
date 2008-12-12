dojo.provide("dojox.data.demos.widgets.FlickrViewList");
dojo.require("dijit._Templated");
dojo.require("dijit._Widget");
dojo.require("dojox.data.demos.widgets.FlickrView");

dojo.declare("dojox.data.demos.widgets.FlickrViewList", [dijit._Widget, dijit._Templated], {
	//Simple demo widget that is just a list of FlickrView Widgets.

	templatePath: dojo.moduleUrl("dojox", "data/demos/widgets/templates/FlickrViewList.html"),

	//Attach points for reference.
	listNode: null,

	postCreate: function(){
		this.fViewWidgets = [];
	},

	clearList: function(){
		while(this.list.firstChild){
			this.list.removeChild(this.list.firstChild);
		}
		for(var i = 0; i < this.fViewWidgets.length; i++){
			this.fViewWidgets[i].destroy();
		}
		this.fViewWidgets = [];
	},

	addView: function(viewData){
		 var newView  = new dojox.data.demos.widgets.FlickrView(viewData);
		 this.fViewWidgets.push(newView);
		 this.list.appendChild(newView.domNode);
	}
});
