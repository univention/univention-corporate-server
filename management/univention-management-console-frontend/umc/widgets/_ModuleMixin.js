/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets._ModuleMixin");

dojo.require("umc.store");
dojo.require("umc.tools");

dojo.declare("umc.widgets._ModuleMixin", null, {
	// summary:
	//		Mixin class for all module classes. It adds some module specific
	//		properties/methods.

	// idProperty: String
	//		Indicates the property to use as the identity property.
	//		The values of this property need to be unique.
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

		this.moduleStore = this.getModuleStore(this.idProperty, this.moduleID, this.moduleFlavor);
	},

	getModuleStore: function(/*String*/ idProperty, /*String?*/ storePath, /*String?*/ moduleFlavor) {
		// summary:
		//		Returns (and if necessary creates) a singleton instance of umc.store.UmcpModuleStore
		//		for the given path to the store and (if specified) the given flavor.
		// idProperty: String
		//		Indicates the property to use as the identity property.
		//		The values of this property need to be unique.
		// storePath: String?
		//		UMCP URL of the module where query, set, remove, put, and add
		//		methods can be found. By default this is the module ID.
		// moduleFlavor: String?
		//		Specifies the module flavor which may need to be communicated to
		//		the server via `umc.tool.umcpCommand()`.
		//		(Is specified automatically.)

		// create a singleton for the module store for each flavor; this is to ensure that
		// the correct flavor of the module is send to the server
		var stores = dojo.getObject('umc.modules._moduleStores', true);
		var key = (storePath || this.moduleID) + '@' + (moduleFlavor || 'default');
		if (!stores[key]) {
			// the store does not exist, we need to create a new singleton
			stores[key] = dojo.store.Observable(new umc.store.UmcpModuleStore({
				idProperty: idProperty,
				storePath: storePath,
				umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
					return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || moduleFlavor );
				}
			}));
		}
		return stores[key];
	},

	umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
		return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || this.moduleFlavor );
	}
});


