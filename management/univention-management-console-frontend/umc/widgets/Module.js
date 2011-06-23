/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.Module");

dojo.require("dijit.layout.StackContainer");
dojo.require("umc.store");
dojo.require("umc.tools");
dojo.require("umc.widgets.StandbyMixin");

dojo.declare("umc.widgets.Module", [ dijit.layout.StackContainer, umc.widgets.StandbyMixin ], {
	// summary:
	//		Basis class for all module classes.
	//		It extends dijit.layout.StackContainer and adds some module specific 
	//		properties/methods.

	// idProperty: String
	//		Indicates the property to use as the identity property. 
	//		The values of this property should be unique.
	idProperty: '',

	// moduleFlavor: String
	//		Specifies the module flavor which may need to be communicated to 
	//		the server via `umc.tool.umcpCommand()`.
	//		(Is specified automatically.)
	moduleFlavor: null,
	
	// moduleID: String
	//		ID of the module.
	//		(Is specified automatically.)
	moduleID: '',

	// moduleStore: umc.store.UmcpModuleStore
	//		A dojo object store interface for query/get/put/remove methods for the UMC
	//		module. Requests for operations on module items should be executed through 
	//		this store interface. In this way, changes will be immediatly reflected to
	//		other parts of the GUI.
	//		(Is specified automatically.)
	moduleStore: null,

	// title: String
	//		Title of the page. This option is necessary for tab pages.
	//		(Is specified automatically.)
	title: '',

	postMixInProperties: function() {
		this.inherited(arguments);

		// create a singleton for the module store at the first call
		var mod = dojo.getObject('umc.modules.' + this.moduleID);
		if (!mod.moduleStore) {
			mod.moduleStore = dojo.store.Observable(new umc.store.UmcpModuleStore({
				idProperty: this.idProperty,
				moduleID: this.moduleID, 
				moduleFlavor: this.moduleFlavor
			}));
		}
		this.moduleStore = mod.moduleStore;

		// set the css class umcModulePane
		//this['class'] = (this['class'] || '') + ' umcModulePane';
	},

	umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
		return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || this.moduleFlavor );
	}
});


