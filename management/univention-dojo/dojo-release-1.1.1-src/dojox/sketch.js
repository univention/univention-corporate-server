dojo.provide("dojox.sketch");
try{
	// fix IE image caching issue
	document.execCommand("BackgroundImageCache", false, true);
}catch(e){ }
dojo.require("dojox.xml.DomParser");
dojo.require("dojox.sketch.UndoStack");
dojo.require("dojox.sketch.Figure");
dojo.require("dojox.sketch.Toolbar");