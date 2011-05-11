/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules");

//dojo.require("umc.widgets");
//dojo.require("umc.tools");
//dojo.require("umc.modules.Module");
//dojo.require("umc.modules.BaseConfigModule");
//dojo.require("dojo.string");
//dojo.require("dojox.layout.TableContainer");
//dojo.require("dijit._Widget");
//dojo.require("dijit.layout.ContentPane");
//dojo.require("dijit.form.TextBox");
//dojo.require("dijit.form.ComboBox");
//dojo.require("dojo.data.ItemFileReadStore");
//dojo.require("dojo.data.ItemFileWriteStore");
////dojo.require("dojox.grid.LazyTreeGrid");
////dojo.require("dojox.grid.TreeGrid");
//dojo.require("dojox.form.CheckedMultiSelect");
//dojo.require("dojox.grid.EnhancedGrid");
//dojo.require("dojox.grid.DataGrid");
//dojo.require("dojox.grid.enhanced.plugins.Menu");
//dojo.require("dojox.grid.enhanced.plugins.IndirectSelection");
////dojo.require("dojox.grid.LazyTreeGridStoreModel");
//dojo.require("dijit.Dialog");
//dojo.require("dijit.tree.ForestStoreModel");

//dojo.declare("MyError", Error, {
//	// summary:
//	//		Convenience error class.
//
//	constructor: function(/*String*/ messageTemplate, /*Array|Object?*/ replaceMap) {
//		// summary:
//		//		Constructor allows to pass only a string, or a string in combination
//		//		with and array/object that can be passed over to dojo.string.substitute().
//		// messageTemplate:
//		//		String with precise error message (and eventually placeholders, e.g., 
//		//		"${0}" or "${aKey}").
//		// replaceMap:
//		//		Array or object that will be passed over to dojo.string.substitute().
//
//		var message = replaceMap !== undefined ? dojo.string.substitute(messageTemplate, replaceMap) : messageTemplate;
//		console.error("NEW ERROR: " + message);
//		this.message = message;
//		this.inherited(message);
//	}
//});

/*
// add categories
umc.modules.ModuleManager.registerCategory("system", "System");
umc.modules.ModuleManager.registerCategory("management", "Management");
umc.modules.ModuleManager.registerCategory("services", "Services");

//TODO: needs to go into the correct .js file
umc.modules.ModuleManager.registerModule(umc.modules.BaseConfigModule, 'baseconfig', 'Univention Configuration Registry', 'system');

dojo.declare("umc.modules.CupsModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.CupsModule, 'cups', 'Drucker Administration', 'management');

dojo.declare("umc.modules.ModutilsModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.ModutilsModule, 'modutils', 'Kernel Module', 'system');

dojo.declare("umc.modules.NagiosModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.NagiosModule, 'nagios', 'Nagios Chart', 'services');

dojo.declare("umc.modules.QuotaModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.QuotaModule, 'quota', 'Dateisystem Quota', 'management');

dojo.declare("umc.modules.VncModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.VncModule, 'vnc', 'VNC', 'management');

dojo.declare("umc.modules.ServicesModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.ServicesModule, 'services', 'System-Dienste', 'system');

dojo.declare("umc.modules.SoftwareMonitorModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.SoftwareMonitorModule, 'softmon', 'Software Monitor', 'system');

dojo.declare("umc.modules.SysInfoModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.SysInfoModule, 'sysinfo', 'Systeminformationen', 'system');

dojo.declare("umc.modules.JoinModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.JoinModule, 'join', 'Domänenbeitritt', 'management');

dojo.declare("umc.modules.PackagesModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.PackagesModule, 'packages', 'Software Management', 'system');

dojo.declare("umc.modules.UpdateModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.UpdateModule, 'update', 'Online-Updates', 'system');

dojo.declare("umc.modules.MrtgModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.MrtgModule, 'mrtg', 'System Statistiken', 'system');

dojo.declare("umc.modules.RebootModule", umc.modules.Module, { });
umc.modules.ModuleManager.registerModule(umc.modules.RebootModule, 'reboot', 'System-Neustart', 'system');
*/
