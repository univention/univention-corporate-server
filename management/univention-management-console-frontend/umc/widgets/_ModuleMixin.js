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

		// create a singleton for the module store for each flavor; this is to ensure that
		// the correct flavor of the module is send to the server
		var path = this.moduleID + '._moduleStores.' + (this.moduleFlavor || 'default');
		this.moduleStore = dojo.getObject(path, false, umc.modules);
		if (!this.moduleStore) {
			this.moduleStore = dojo.store.Observable(new umc.store.UmcpModuleStore({
				idProperty: this.idProperty,
				storePath: this.moduleID,
				umcpCommand: dojo.hitch(this, 'umcpCommand')
			}));
			dojo.setObject(path, this.moduleStore, umc.modules);
		}

		// set the css class umcModulePane
		//this['class'] = (this['class'] || '') + ' umcModulePane';
	},

	umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor ) {
		return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || this.moduleFlavor );
	}
});


