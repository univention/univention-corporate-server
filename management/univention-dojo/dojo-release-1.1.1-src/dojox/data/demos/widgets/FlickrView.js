dojo.provide("dojox.data.demos.widgets.FlickrView");
dojo.require("dijit._Templated");
dojo.require("dijit._Widget");

dojo.declare("dojox.data.demos.widgets.FlickrView", [dijit._Widget, dijit._Templated], {
	//Simple demo widget for representing a view of a Flickr Item.

	templatePath: dojo.moduleUrl("dojox", "data/demos/widgets/templates/FlickrView.html"),

	//Attach points for reference.
	titleNode: null, 
	descriptionNode: null,
	imageNode: null,
	authorNode: null,

	title: "",
	author: "",
	imageUrl: "",
	iconUrl: "",

	postCreate: function(){
		this.titleNode.appendChild(document.createTextNode(this.title));
		this.authorNode.appendChild(document.createTextNode(this.author));
		var href = document.createElement("a");
		href.setAttribute("href", this.imageUrl);
		href.setAttribute("target", "_blank");
        var imageTag = document.createElement("img");
		imageTag.setAttribute("src", this.iconUrl);
		href.appendChild(imageTag);
		this.imageNode.appendChild(href);
	}
});
