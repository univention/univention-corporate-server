/*global console MyError dojo dojox dijit umc2 */

dojo.provide("umc2.modules");

//dojo.require("umc2.widgets");
//dojo.require("umc2.tools");
//dojo.require("umc2.modules.Module");
//dojo.require("umc2.modules.BaseConfigModule");
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
umc2.modules.ModuleManager.registerCategory("system", "System");
umc2.modules.ModuleManager.registerCategory("management", "Management");
umc2.modules.ModuleManager.registerCategory("services", "Services");

//TODO: needs to go into the correct .js file
umc2.modules.ModuleManager.registerModule(umc2.modules.BaseConfigModule, 'baseconfig', 'Univention Configuration Registry', 'system');

dojo.declare("umc2.modules.CupsModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.CupsModule, 'cups', 'Drucker Administration', 'management');

dojo.declare("umc2.modules.ModutilsModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.ModutilsModule, 'modutils', 'Kernel Module', 'system');

dojo.declare("umc2.modules.NagiosModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.NagiosModule, 'nagios', 'Nagios Chart', 'services');

dojo.declare("umc2.modules.QuotaModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.QuotaModule, 'quota', 'Dateisystem Quota', 'management');

dojo.declare("umc2.modules.VncModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.VncModule, 'vnc', 'VNC', 'management');

dojo.declare("umc2.modules.ServicesModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.ServicesModule, 'services', 'System-Dienste', 'system');

dojo.declare("umc2.modules.SoftwareMonitorModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.SoftwareMonitorModule, 'softmon', 'Software Monitor', 'system');

dojo.declare("umc2.modules.SysInfoModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.SysInfoModule, 'sysinfo', 'Systeminformationen', 'system');

dojo.declare("umc2.modules.JoinModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.JoinModule, 'join', 'Domänenbeitritt', 'management');

dojo.declare("umc2.modules.PackagesModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.PackagesModule, 'packages', 'Software Management', 'system');

dojo.declare("umc2.modules.UpdateModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.UpdateModule, 'update', 'Online-Updates', 'system');

dojo.declare("umc2.modules.MrtgModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.MrtgModule, 'mrtg', 'System Statistiken', 'system');

dojo.declare("umc2.modules.RebootModule", umc2.modules.Module, { });
umc2.modules.ModuleManager.registerModule(umc2.modules.RebootModule, 'reboot', 'System-Neustart', 'system');
*/
