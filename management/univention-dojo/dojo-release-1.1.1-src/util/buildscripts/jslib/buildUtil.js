var buildUtil = {};

//Default build options.
buildUtil.DojoBuildOptions = {
	"profile": {
		defaultValue: "base",
		helpText: "The name of the profile to use for the build. It must be the first part of "
			+ "the profile file name in the profiles/ directory. For instance, to use base.profile.js, "
			+ "specify profile=base."
	},
	"profileFile": {
		defaultValue: "",
		helpText: "A file path to the the profile file. Use this if your profile is outside of the profiles "
			+ "directory. Do not specify the \"profile\" build option if you use \"profileFile\"."
	},
	"action": {
		defaultValue: "help",
		helpText: "The build action(s) to run. Can be a comma-separated list, like action=clean,release. "
			+ "The possible build actions are: clean, release."
	},
	"version": {
		defaultValue: "0.0.0.dev",
		helpText: "The build will be stamped with this version string."
	},
	"localeList": {
		defaultValue: "ar,cs,da,de-de,el,en-gb,en-us,es-es,fi-fi,fr-fr,he-il,hu,it-it,ja-jp,ko-kr,nl-nl,no,pl,pt-br,pt-pt,ru,sv,tr,zh-tw,zh-cn",
		helpText: "The set of locales to use when flattening i18n bundles."
	},
	
	"releaseName": {
		defaultValue: "dojo",
		helpText: "The name of the release. A directory inside 'releaseDir' will be created with this name."
	},
	"releaseDir": {
		defaultValue: "../../release/",
		helpText: "The top level release directory where builds end up. The 'releaseName' directories will "
			+ " be placed inside this directory."
	},
	"loader": {
		defaultValue: "default",
		helpText: "The type of dojo loader to use. \"default\" or \"xdomain\" are acceptable values."		
	},
	"internStrings": {
		defaultValue: true,
		helpText: "Turn on or off widget template/dojo.uri.cache() file interning."
	},
	"optimize": {
		defaultValue: "",
		helpText: "Specifies how to optimize module files. If \"comments\" is specified, "
			+ "then code comments are stripped. If \"shrinksafe\" is specified, then "
			+ "the Dojo compressor will be used on the files, and line returns will be removed. "
			+ "If \"shrinksafe.keepLines\" is specified, then the Dojo compressor will be used "
			+ "on the files, and line returns will be preserved. If \"packer\" is specified, "
			+ "Then Dean Edwards' Packer will be used."
	},
	"layerOptimize": {
		defaultValue: "shrinksafe",
		helpText: "Specifies how to optimize the layer files. If \"comments\" is specified, "
			+ "then code comments are stripped. If \"shrinksafe\" is specified, then "
			+ "the Dojo compressor will be used on the files, and line returns will be removed. "
			+ "If \"shrinksafe.keepLines\" is specified, then the Dojo compressor will be used "
			+ "on the layer files, and line returns will be preserved. If \"packer\" is specified, "
			+ "Then Dean Edwards' Packer will be used."
	},
	"cssOptimize": {
		defaultValue: "",
		helpText: "Specifies how to optimize CSS files. If \"comments\" is specified, "
			+ "then code comments and line returns are stripped, and files referenced via @import "
			+ "are inlined. If \"comments.keepLines\" "	
			+ "is specified, then code comments are stripped and @import calls are inlined, but line returns are preserved."
	},

	"cssImportIgnore": {
		defaultValue: "",
		helpText: "If using cssOptimize=\"comments\", then you can force the @import inlining step "
			+ "to ignore a set of files by using this option. The value of this option should be a comma "	
			+ "separated list of CSS files names to ignore. The file names should match whatever strings "
			+ "are used for the @import calls."
	},

	"copyTests": {
		defaultValue: true,
		helpText: "Turn on or off copying of test files."
	},
	"log": {
		defaultValue: logger.TRACE,
		helpText: "Sets the logging verbosity. See jslib/logger.js for possible integer values."
	},
	"xdDojoPath": {
		defaultValue: "",
		helpText: "If the loader=xdomain build option is used, then the value of this option "
			+ "will be used to call dojo.registerModulePath() for dojo, dijit and dojox. "
			+ "The xdDojoPath should be the directory that contains the dojo, dijit and dojox "
			+ "directories, and it should NOT end in a slash. For instance: 'http://some.domain.com/path/to/dojo090'."
	},
	"symbol": {
		defaultValue: "",
		helpText: "Inserts function symbols as global references so that anonymous "
			+ "functions will show up in all debuggers (esp. IE which does not attempt "
			+ "to infer function names from the context of their definition). Valid values "
			+ "are \"long\" and \"short\". If \"short\" is used, then a symboltables.txt file "
			+ "will be generated in each module prefix's release directory which maps the "
			+ "short symbol names to more descriptive names."
	},
	"scopeDjConfig": {
		defaultValue: "",
		helpText: "Burn in a djConfig object into the built dojo.js file. Useful if you are making your own scoped dojo and you want a "
			+ "djConfig object local to your version that will not be affected by any globally declared djConfig object in the page. "
			+ "Value must be a string that will look like a javascript object literal once it is placed in the built source. "
			+ "use Dojo as part of a JS library, but want to make a self-contained library with no external dojo/dijit/dojox. Example "
			+ "(note that the backslashes below are required to avoid shell escaping if you type this on the command line):\n"
			+ "scopeDjConfig={isDebug:true,scopeMap:[[\\\"dojo\\\",\\\"mydojo\\\"],[\\\"dijit\\\",\\\"mydijit\\\"],[\\\"dojox\\\",\\\"mydojox\\\"]]}"
	},
	"scopeMap": {
		defaultValue: "",
		helpText: "Change the default dojo, dijit and dojox scope names to something else. Useful if you want to "
			+ "use Dojo as part of a JS library, but want to make a self-contained library with no external dojo/dijit/dojox "
			+ "references. Format is a string that contains no spaces, and is similar to the djConfig.scopeMap value (note that the "
			+ "backslashes below are required to avoid shell escaping):\n"
			+ "scopeMap=[[\\\"dojo\\\",\\\"mydojo\\\"],[\\\"dijit\\\",\\\"mydijit\\\"],[\\\"dojox\\\",\\\"mydojox\\\"]]"
	},
	"xdScopeArgs": {
		defaultValue: "",
		helpText: "If the loader=xdomain build option is used, then the value of this option "
			+ "will be used as the arguments to the function that defines the modules in the .xd.js files. "
			+ "This allows for more than one version of the same module to be in a page. See documentation on "
			+ "djConfig.scopeMap for more information."
	},
	"xdDojoScopeName": {
		defaultValue: "dojo",
		helpText: "If the loader=xdomain build option is used, then the value of this option "
			+ "will be used instead of 'dojo' for the 'dojo._xdResourceLoaded()' calls that are done in the .xd.js files. "
			+ "This allows for dojo to be under a different scope name but still allow xdomain loading with that scope name."
	},
	"buildLayers": {
		defaultValue: "",
		helpText: "A comma-separated list of layer names to build. Using this option means that only those layers will be built. "
			+ "This helps if you are doing quick development and test cycles with layers. If you have problems using this option, "
			+ "try removing it and doing a full build with action=clean,release. This build option assumes you have done at least one full build first."
	}
};

buildUtil.makeBuildOptions = function(/*Array*/scriptArgs){
	//summary: constructs the build options by combining the scriptArgs with
	//default build options and anything specified in a profile file.

	var kwArgs = {};

	//Parse the command line arguments
	var kwArgs = buildUtil.convertArrayToObject(scriptArgs);
	if(!kwArgs["profileFile"] && kwArgs["profile"]){
		kwArgs.profileFile = "profiles/" + kwArgs.profile + ".profile.js";
	}

	//Load dependencies object from profile file, if there is one.
	var dependencies = {};
	if(kwArgs["profileFile"]){
		var profileProperties = buildUtil.evalProfile(kwArgs.profileFile);
		if(profileProperties){
			kwArgs.profileProperties = profileProperties;
			dependencies = kwArgs.profileProperties.dependencies;
			
			//Allow setting build options from on the profile's dependencies object
			for(var param in dependencies){
				if(param != "layers" && param != "prefixes"){
					kwArgs[param] = dependencies[param];
				}
			}
		}
	}

	//Set up default options
	for(var param in buildUtil.DojoBuildOptions){
		//Only use default if there is no value so far.
		if(typeof kwArgs[param] == "undefined"){
			kwArgs[param] = buildUtil.DojoBuildOptions[param].defaultValue;
		}else if(kwArgs[param] === "false"){
			//Make sure "false" strings get translated to proper false value.
			kwArgs[param] = false;
		}
	}

	//Set up some compound values
	kwArgs.releaseDir += kwArgs["releaseName"];
	kwArgs.action = kwArgs.action.split(",");
	kwArgs.localeList = kwArgs.localeList.split(",");
	
	//Attach the final loader type to the dependencies
	dependencies.loader = kwArgs.loader;

	return kwArgs;
}

buildUtil.interningDojoUriRegExpString = "(((templatePath|templateCssPath)\\s*(=|:)\\s*)|dojo\\.uri\\.cache\\.allow\\(\\s*)dojo\\.(module)?Url\\(\\s*?[\\\"\\']([\\w\\.\\/]+)[\\\"\\'](([\\,\\s]*)[\\\"\\']([\\w\\.\\/]*)[\\\"\\'])?\\s*\\)";
buildUtil.interningGlobalDojoUriRegExp = new RegExp(buildUtil.interningDojoUriRegExpString, "g");
buildUtil.interningLocalDojoUriRegExp = new RegExp(buildUtil.interningDojoUriRegExpString);

//Even though these are i18n-specific, they are not in i18nUtil.js since one is referenced
//in this file. Want to avoid circular dependency loading issues.
buildUtil.masterRequireLocalizationRegExpString = "dojo.(requireLocalization)\\(([\\w\\W]*?)\\)";
buildUtil.globalRequireLocalizationRegExp = new RegExp(buildUtil.masterRequireLocalizationRegExpString, "mg");
buildUtil.requireLocalizationRegExp = new RegExp(buildUtil.masterRequireLocalizationRegExpString);

//FIXME: This should take the build kwArgs now instead.
buildUtil.getDojoLoader = function(/*Object?*/dependencies){
	//summary: gets the type of Dojo loader for the build. For example default or
	//xdomain loading. Override for web builds.
	return (dependencies && dependencies["loader"] ? dependencies["loader"] : java.lang.System.getProperty("DOJO_LOADER"));
}

buildUtil.includeLoaderFiles = function(/*String*/dojoLoader, /*String or Array*/hostenvType, /*String*/buildscriptsPath){
	//summary: adds the loader files to the file list for a build file.
	dojo._loadedUrls.push(buildscriptsPath + "jslib/dojoGuardStart.jsfrag");
	dojo._loadedUrls.push(buildscriptsPath + "../../dojo/_base/_loader/bootstrap.js");
	
	if(dojoLoader == "default"){
		dojo._loadedUrls.push(buildscriptsPath + "../../dojo/_base/_loader/loader.js");
	}else if(dojoLoader == "xdomain"){
		dojo._loadedUrls.push(buildscriptsPath + "../../dojo/_base/_loader/loader.js");
		dojo._loadedUrls.push(buildscriptsPath + "../../dojo/_base/_loader/loader_xd.js");
	}

	if(hostenvType.constructor == Array){
		for(var x=0; x<hostenvType.length; x++){
			dojo._loadedUrls.push(buildscriptsPath + "../../dojo/_base/_loader/hostenv_"+hostenvType[x]+".js");
		}
		hostenvType = hostenvType.pop();
	}else{
		dojo._loadedUrls.push(buildscriptsPath + "../../dojo/_base/_loader/hostenv_"+hostenvType+".js");
	}
}

buildUtil.getDependencyList = function(/*Object*/dependencies, /*String or Array*/hostenvType, /*Object?*/kwArgs, /*String?*/buildscriptsPath){
	//summary: Main function that traces the files that are needed for a give list of dependencies.

	if(!dependencies){
		dependencies = {}
	}

	buildscriptsPath = buildscriptsPath || "./";
	
	var dojoLoader = buildUtil.getDojoLoader(dependencies);
	if(!dojoLoader || dojoLoader=="null" || dojoLoader==""){
		dojoLoader = "default";
	}


	//Now build the URI list, starting with the main dojo.js file
	if(!dependencies["layers"]){
		dependencies.layers = [];
	}

	//Set up the dojo.js layer. Add _base if the profile already
	//defines a dojo.js layer. If the profile defines a dojo.js
	//layer it MUST be the first layer.
	if(dependencies.layers[0] && dependencies.layers[0].name == "dojo.js"){
		if(!dependencies.layers[0].customBase){
			dependencies.layers[0].dependencies.unshift("dojo._base");
		}
	}else{
		dependencies.layers.unshift({
			name: "dojo.js",
			dependencies: [
				"dojo._base"
			]
		});
	}

	currentProvideList = [];
	var result = [];
	var layers = dependencies["layers"];
	var layerCount = layers.length;
	
	//Process dojo layer files 
	if(layerCount){
		//Set up a lookup table for the layer URIs based on layer file name.
		var namedLayerUris = {};
				
		//If xd build, cycle over the layers twice. Second time through
		//are the xd files.
		var endCount = layerCount;
		if(dojoLoader == "xdomain"){
			endCount = endCount * 2;
		}
		
		for(var i = 0; i < endCount; i++){
			var j = i;
			var isXd = false;
			if(i >= layerCount){
				//Dealing with the xd files.
				if(i == layerCount){
					//Reset the dependencies.
					namedLayerUris = {};
				}
				j = i - layerCount;
				isXd = true;
			}
			var layer = layers[j];
			var layerName = layers[j].name;
			if(isXd){
				layerName = layerName.replace(/\.js$/, ".xd.js");
			}

			//Add dojo.i18n to dojo.xd.js. Too complicated to dynamically load it in that case.
			if(isXd && layerName == "dojo.xd.js"){
				layer.dependencies.splice(1, 0, "dojo.i18n");
			}

			djConfig = {
				baseRelativePath: "../../dojo/"
				// isDebug: true
			};

	
			load(buildscriptsPath + "../../dojo/_base/_loader/bootstrap.js");
			load(buildscriptsPath + "../../dojo/_base/_loader/loader.js");
			load(buildscriptsPath + "../../dojo/_base/_loader/hostenv_rhino.js");
			dojo.global = {};

		
			if(!hostenvType){
				hostenvType = "browser";
			}
		
			if(dependencies["prefixes"]){
				var tmp = dependencies.prefixes;
				for(var x=0; x<tmp.length; x++){
					dojo.registerModulePath(tmp[x][0], tmp[x][1]);
				}
			}
		
			dojo._name = hostenvType;
			if(hostenvType == "browser"){
				//Make sure we setup the env so that dojo
				//thinks we are running in a browser.
				dojo.isBrowser = true;
			}
			
			//Override dojo.provide to get a list of resource providers.
			var currentProvideList = [];
			dojo._provide = dojo.provide;
			dojo.provide = function(resourceName){
				currentProvideList.push(resourceName);
				dojo._provide(resourceName);
			}
			
			// over-write dojo.eval to prevent actual loading of subsequent files
			dojo._oldEval = dojo["eval"];
			dojo["eval"] = function(){ return true; }
			var old_load = load;
			load = function(uri){
				try{
					//Strip comments and apply conditional directives before tracing the dependencies.
					var text = fileUtil.readFile(uri);
					var text = (kwArgs ? buildUtil.processConditionals(layerName, text, kwArgs) : text);
					var text = buildUtil.removeComments(text);

					var requires = dojo._getRequiresAndProvides(text);
					eval(requires.join(";"));
					dojo._loadedUrls.push(uri);
					dojo._loadedUrls[uri] = true;
					var delayRequires = dojo._getDelayRequiresAndProvides(text);
					
					//Now do the requireIfs. Since they contain some code tests that could
					//not be valid in the current scope (access variables that are not defined
					//when running in Rhino, for instance), then do a try/catch around each
					//one. If the expression fails, then it was not meant for this context.
					for(var i = 0; i < delayRequires.length; i++){
						try{
							eval(delayRequires[i]);
						}catch(e){
							//logger.trace("A requireIf failed for text [" + delayRequires[i] + "], error: " + e);
						}
					}
				}catch(e){
					java.lang.System.err.println("error loading uri: " + uri + ", exception: " + e);
					quit(-1);
				}
				return true;
			}

			dojo._getRequiresAndProvides = function(contents){
				// FIXME: should probably memoize this!
				if(!contents){ return []; }
			
				// check to see if we need to load anything else first. Ugg.
				var deps = [];
				var tmp;
				RegExp.lastIndex = 0;
				var testExp = /dojo.(require|platformRequire|provide)\([\w\W]*?\)/mg;
				while((tmp = testExp.exec(contents)) != null){
					deps.push(tmp[0]);
				}
				
				//If there is a dojo.requireLocalization() call, make sure to add dojo.i18n
				if(contents.match(/dojo\.requireLocalization\(.*?\)/)){
					deps.push('dojo.require("dojo.i18n")');
				}
		
				return deps;
			}
			
			dojo._getDelayRequiresAndProvides = function(contents){
				// FIXME: should probably memoize this!
				if(!contents){ return []; }
			
				// check to see if we need to load anything else first. Ugg.
				var deps = [];
				var tmp;
				RegExp.lastIndex = 0;
				var testExp = /dojo.(requireAfterIf|requireIf)\([\w\W]*?\)/mg;
				while((tmp = testExp.exec(contents)) != null){
					deps.push(tmp[0]);
				}
				return deps;
			}
		
			if(dependencies["dojoLoaded"]){
				dependencies["dojoLoaded"]();
			}
		
			
			//Add the loader files if this is a loader layer.
			if(layerName == "dojo.js"){
				buildUtil.includeLoaderFiles("default", hostenvType, buildscriptsPath);
			}else if(layerName == "dojo.xd.js"){
				buildUtil.includeLoaderFiles("xdomain", hostenvType, buildscriptsPath);
			}
		
			//Set up list of module URIs that are already defined for this layer's
			//layer dependencies. Always include the dojo.js layer uris. dojo.js could
			//have more than _base, and in xdomain, it has dojo.i18n.
			var layerUris = [];
			if(layer.name != "dojo.js"){
				layerUris = layerUris.concat(namedLayerUris["dojo.js"]);
			}
			
			if(layer["layerDependencies"]){
				for(var j = 0; j < layer.layerDependencies.length; j++){
					if(namedLayerUris[layer.layerDependencies[j]]){
						layerUris = layerUris.concat(namedLayerUris[layer.layerDependencies[j]]);
					}
				}
			}

			//Get the final list of dependencies in this layer
			var depList = buildUtil.determineUriList(layer.dependencies, layerUris, dependencies["filters"]); 
			
			
			//If dojo.xd.js, need to put dojo.i18n before the code in dojo._base.browser that does the 
			//auto dojo.require calls based on dojo.config.require array.
			//This is a little bit hackish, but it allows dojo.i18n to use any Base methods
			//in the future.
			if(layerName == "dojo.xd.js"){
				//Find the dojo.i18n line. Start at the end of depList because it is likely closer
				//to the end than the beginning.
				var i18nXdEntry = null;
				for(var i18nIndex = depList.length - 1; i18nIndex >= 0; i18nIndex--){
					if(depList[i18nIndex].match(/\/dojo\/i18n\.js$/)){
						i18nXdEntry = depList.splice(i18nIndex, 1)[0];
						break;
					}
				}
				
				//Only operate if we have an i18n entry. We may allow building without
				//dojo.i18n as part of the xd file.
				if(i18nXdEntry){
					for(i18nIndex = depList.length - 1; i18nIndex >= 0; i18nIndex--){
						if(depList[i18nIndex].match(/dojo\/_base\/browser\.js$/)){
							depList.splice(i18nIndex, 0, i18nXdEntry);
							break;
						}
					}
				}
			}
			
			
			//Add the final closure guard to the list.
			if(layerName == "dojo.js" || layerName == "dojo.xd.js"){
				depList.push(buildscriptsPath + "jslib/dojoGuardEnd.jsfrag");
			}

			//Store the layer URIs that are in this file as well as all files it depends on.
			namedLayerUris[layer.name] = layerUris.concat(depList);
		
			//Add to the results object.
			if(!layer["discard"]){
				result.push({
					layerName: layerName,
					resourceName: layer.resourceName,
					copyrightFile: layer.copyrightFile,
					depList: depList,
					provideList: currentProvideList
				});
			}

			//Reset for another run through the loop.
			currentProvideList = []; 

			load = old_load; // restore the original load function
			dojo["eval"] = dojo._oldEval; // restore the original dojo.eval function
	
			var djGlobal = dojo.global;
			djGlobal['djConfig'] = undefined;
	
			delete dojo;
		}
	}

	return result; //Object with properties: name (String), depList (Array) and provideList (Array)
}

buildUtil.removeComments = function(/*String*/contents){
	//summary: strips JS comments from a string. Not bulletproof, but does a good enough job
	//for stripping out stuff that is not related to mapping resource dependencies.

	//If we get the contents of the file from Rhino, it might not be a JS
	//string, but rather a Java string, which will cause the replace() method
	//to bomb.
	contents = contents ? new String(contents) : "";
	//clobber all comments
	return contents.replace( /(\/\*([\s\S]*?)\*\/|\/\/(.*)$)/mg , "");
}

//Function to do the actual collection of file names to join.
buildUtil.determineUriList = function(/*Array*/dependencies, /*Array*/layerUris, /*Object*/filters){
	for(var x=0; x<dependencies.length; x++){
		try{
			var dep = dependencies[x];

			//Don't process loader_xd.js since it has some regexps 
			//and mentions of dojo.require/provide, which will cause 
			//havoc in the dojo._loadModule() method.
			if(dep.indexOf("loader_xd.js") == -1){
				dojo._loadModule(dep, true);
			}
		}catch(e){
			java.lang.System.err.println("Error loading module!" + e);
			quit(-1);
		}
	}

	var depList = [];
	var seen = {};
	uris: for(var x=0; x<dojo._loadedUrls.length; x++){
		var curi = dojo._loadedUrls[x];
		if(!seen[curi]){
			seen[curi] = true;
			if(filters){
				for(var i in filters){
					if(curi.match(filters[i])){
						continue uris;
					}
				}
			}
			
			//If the uri is already accounted for in another
			//layer, skip it.
			if(layerUris){
				for(var i = 0; i < layerUris.length; i++){ 
					if(curi == layerUris[i]){ 
						continue uris; 
					} 
				} 
			} 

			//No filter or layerUri matches, so it is good to keep.
			depList.push(curi);
		}
	}
	
	//Clear out the loadedUris for the next run. 
	dojo._loadedUrls = []; 
	return depList; 
}


buildUtil.evalProfile = function(/*String*/profileFile, /*Boolean*/fileIsProfileText){
	var dependencies = {};
	var hostenvType = null;
	var profileText = fileIsProfileText ? profileFile : fileUtil.readFile(profileFile);

	//Remove the call to getDependencyList.js because it is not supported anymore.
	profileText = profileText.replace(/load\(("|')getDependencyList.js("|')\)/, "");
	eval(profileText);
	
	//Build up the prefixes so the rest of the scripts
	//do not have to guess where things are at.
	if(!dependencies["prefixes"]){
		dependencies.prefixes = [];
	}
	
	//Find prefixes that are used.
	var usedPrefixes = ["dojo"];
	usedPrefixes._entries = { dojo: true };
	
	//Check normal dependencies.
	buildUtil.addPrefixesFromDependencies(usedPrefixes, dependencies);

	//Check layer dependencies
	var layerDeps = dependencies.layers;
	
	if(layerDeps){
		for(var i = 0; i < layerDeps.length; i++){
			buildUtil.addPrefixesFromDependencies(usedPrefixes, layerDeps[i].dependencies);
		}
	}

	//Now add to the real prefix array.
	//If not already in the prefix array, assume the default
	//location, as a sibling to dojo (and util).
	for(var i = 0; i < usedPrefixes.length; i++){
		var hasPrefix = false;
		for(var j = 0; j < dependencies.prefixes.length; j++){
			if(dependencies.prefixes[j][0] == usedPrefixes[i]){
				hasPrefix = true;
				break;
			}
		}
		if(!hasPrefix){
			//Assumptions are that any prefixes that are not dojo
			//are a sibling to dojo. Dojo path is special, it needs
			//to be relative to util/buildscripts. The dojo path is
			//prepended to other paths later.
			var dirPrefix = "../";
			if(usedPrefixes[i] == "dojo"){
				dirPrefix = "../../";
			}
			dependencies.prefixes.push([usedPrefixes[i], dirPrefix + usedPrefixes[i]]);
		}
	}

	return {
		dependencies: dependencies,
		hostenvType: hostenvType
	};
}

buildUtil.getDojoPrefixPath = function(/*Array*/prefixes){
	//summary: Gets the path to Dojo from the prefixes.
	var result = null;
	for(var i = 0; i < prefixes.length; i++){
		if(prefixes[i][0] == "dojo"){
			result = prefixes[i][1];
			break;
		}
	}
	return result;
}

buildUtil.addPrefixesFromDependencies = function(/*Array*/prefixStore, /*Array*/dependencies){
	//summary: finds the top level prefixes in the build process that
	//we need to track for the build process. 
	for(var i = 0; i < dependencies.length; i++){
		var topPrefix = dependencies[i].split(".")[0];
		if(!prefixStore._entries[topPrefix]){
			prefixStore.push(topPrefix);
			prefixStore._entries[topPrefix] = true;
		}
	}
}

buildUtil.loadDependencyList = function(/*Object*/profile, /*Object?*/kwArgs, /*String?*/buildscriptsPath){
	//summary: Traverses the dependencies in the profile object.
	//profile:
	//		The profile object that is a result of a buildUtil.evalProfile() call.
	var depResult = buildUtil.getDependencyList(profile.dependencies, profile.hostenvType, kwArgs, buildscriptsPath);
	depResult.dependencies = profile.dependencies;
	
	return depResult;
}

buildUtil.createLayerContents = function(
	/*String*/layerName,
	/*String*/resourceName,
	/*Array*/depList,
	/*Array*/provideList,
	/*String*/version,
	/*Object?*/kwArgs){
	//summary: Creates the core contents for a build layer (including dojo.js).

	//Concat the files together, and mark where we should insert all the
	//provide statements.
	var dojoContents = resourceName ? "dojo.provide(\"" + resourceName + "\");\r\n" : "";
	for(var i = 0; i < depList.length; i++){
		//Run the file contents through the include/exclude "preprocessor".
		var depContents = fileUtil.readFile(depList[i]);
		dojoContents += (kwArgs ? buildUtil.processConditionals(layerName, depContents, kwArgs) : depContents)
			+ "\r\n";
	}

	//Construct a string of all the dojo.provide statements.
	//This string will be used to construct the regexp that will be
	//used to remove matching dojo.require statements.
	//Sort the provide list alphabetically to make it easy to read.
	//Order of provide statements do not matter.
	provideList = provideList.sort(); 
	var depRegExpString = "";
	for(var i = 0; i < provideList.length; i++){
		if(i != 0){
			depRegExpString += "|";
		}
		depRegExpString += '([\'"]' + provideList[i] + '[\'"])';
	}
		
	//If we have a string for a regexp, do the dojo.require() and requireIf() removal now.
	if(depRegExpString){
		//Make to escape regexp-sensitive characters
		depRegExpString = buildUtil.regExpEscape(depRegExpString);
		//Build the regexp
		var depRegExp = new RegExp("dojo\\.(require|requireIf)\\(.*?(" + depRegExpString + ")\\)(;?)", "g");
		dojoContents = dojoContents.replace(depRegExp, "");
	}

	//Set version number.
	dojoContents = buildUtil.changeVersion(version, dojoContents);

	return dojoContents; //String
}

buildUtil.changeVersion = function(/*String*/version, /*String*/fileContents){
	//summary: Changes the version number for dojo. Input should be the fileContents
	//of a file that contains the version number.
	
	//Set version number.
	//First, break apart the version string.
	var verSegments = version.match(/^(\d*)\.?(\d*)\.?(\d*)\.?(.*)$/); 
	var majorValue = verSegments[1] || 0; 
	var minorValue = verSegments[2] || 0; 
	var patchValue = verSegments[3] || 0; 
	var flagValue  = verSegments[4] || ""; 

	//Do the final version replacement.
	fileContents = fileContents.replace(
		/major:\s*\d*,\s*minor:\s*\d*,\s*patch:\s*\d*,\s*flag:\s*".*?"\s*,/g,
		"major: " + majorValue + ", minor: " + minorValue + ", patch: " + patchValue + ", flag: \"" + flagValue + "\","
	);

	return fileContents; //String
}

buildUtil.makeDojoJs = function(/*Object*/dependencyResult, /*String*/version, /*Object?*/kwArgs){
	//summary: Makes the uncompressed contents for dojo.js using the object
	//returned from buildUtil.getDependencyList()

	var lineSeparator = fileUtil.getLineSeparator();

	//Cycle through the layers to create the content for each layer.
	for(var i = 0; i< dependencyResult.length; i++){
		var layerResult = dependencyResult[i];
		layerResult.contents = buildUtil.createLayerContents(layerResult.layerName, layerResult.resourceName, layerResult.depList, layerResult.provideList, version, kwArgs);
	}

	//Object with properties:
	//depList: Array of file paths (src/io/js)
	//provideList: Array of module resource names (dojo.io)
	//name: name of the layer file
	//contents: the file contents for that layer file.
	return dependencyResult; 

	//Return the dependency list, since it is used for other things in the ant file.
	return {
		resourceDependencies: depList,
		dojoContents: dojoContents
	};
}


buildUtil.getDependencyPropertyFromProfile = function(/*String*/profileFile, /*String*/propName){
	//summary: Gets a dependencies property from the profile file. The value
	//of the property is assumed to be an array. An array will always be returned,
	//but it may be an empty array.

	//Use new String to make sure we have a JS string (not a Java string)
	var profileText = fileUtil.readFile(profileFile);
	//Get rid of CR and LFs since they seem to mess with the regexp match.
	//Using the "m" option on the regexp was not enough.
	profileText = profileText.replace(/\r/g, "");
	profileText = profileText.replace(/\n/g, "");


	var result = [];
	var matchRegExp = new RegExp("(dependencies\\." + propName + "\\s*=\\s*\\[[^;]*\\s*\\])", "m");

	var matches = profileText.match(matchRegExp);
	//Create a shell object to hold the evaled properties.
	var dependencies = {};
	
	if(matches && matches.length > 0){
		eval(matches[0]);
		if(dependencies && dependencies[propName] && dependencies[propName].length > 0){
			result = dependencies[propName];
		}
	}

	return result; //Array
}

buildUtil.configPrefixes = function(/*Object*/prefixes){
	//summary: Registers the prefixes with Dojo.
	if(prefixes && prefixes.length > 0){
		for(i = 0; i < prefixes.length; i++){
			dojo.registerModulePath(prefixes[i][0], prefixes[i][1]);
		}
	}
}


//The regular expressions that will help find dependencies in the file contents.
buildUtil.masterDependencyRegExpString = "dojo.(requireLocalization|require|requireIf|provide|requireAfterIf|platformRequire|i18n\._preloadLocalizations)\\(([\\w\\W]*?)\\)";
buildUtil.globalDependencyRegExp = new RegExp(buildUtil.masterDependencyRegExpString, "mg");
buildUtil.dependencyPartsRegExp = new RegExp(buildUtil.masterDependencyRegExpString);

buildUtil.mapPathToResourceName = function(pathName, prefixes){
	//summary: converts a path name to the best fit for a resource name
	//based on the available prefixes.
	//Returns a value like "foo.bar" given an input of /some/path/to/foo/bar.js"

	//First, find best fit prefix.
	var bestPrefix = "";
	var bestPrefixPath = "";
	var bestPrefixPathIndex = 0;
	var currentIndex = 0;
	for(var i = 0; i < prefixes.length; i++){
		//Prefix path must match somewhere in the pathName
		currentIndex = pathName.lastIndexOf("/" + prefixes[i][0].replace(/\./g, "/") + "/");
		if(currentIndex != -1 && currentIndex > bestPrefixPathIndex){
			bestPrefix = prefixes[i][0];
			bestPrefixPath = prefixes[i][1];
			bestPrefixPathIndex = currentIndex;
		}
	}
	
	//Adjust the bestPrefixPathIndex by 2, to account for the slashes in the test above.
	bestPrefixPathIndex += 2;
	
	if(!bestPrefix){
		throw "Could not find a matching prefix for pathName: " + pathName;
	}
	
	//Strip off first part of file name that is not relevant.
	var startIndex = bestPrefixPathIndex + bestPrefix.length;
	var newPathName = pathName.substring(startIndex, pathName.length);
	
	//Remove file extensions and any front slash.
	newPathName = newPathName.replace(/^\//, "").replace(/\..*?$/, "");
	
	return bestPrefix + "." + newPathName.replace(/\//g, "."); 
}

buildUtil.mapResourceToPath = function(resourceName, prefixes){
	//summary: converts a resourceName to a path.
	//resourceName: String: like dojo.foo or mymodule.bar
	//prefixes: Array: Actually an array of arrays. Comes from profile js file.
	//          dependencies.prefixes = [["mymodule.foo", "../mymoduledir"]];
	
	var bestPrefix = "";
	var bestPrefixPath = "";
	if(prefixes){
		for(var i = 0; i < prefixes.length; i++){
			//Prefix must match from the start of the resourceName string.
			if(resourceName.indexOf(prefixes[i][0]) == 0){
				if(prefixes[i][0].length > bestPrefix.length){
					bestPrefix = prefixes[i][0];
					bestPrefixPath = prefixes[i][1];
				}
			}
		}
	}

	//Get rid of matching prefix from resource name.
	resourceName = resourceName.replace(bestPrefix, "");
	
	if(resourceName.charAt(0) == '.'){
		resourceName = resourceName.substring(1, resourceName.length);
	}
	
	resourceName = resourceName.replace(/\./g, "/");

	var finalPath = bestPrefixPath;
	if(finalPath.charAt(finalPath.length - 1) != "/"){
		finalPath += "/";
	}
	if (resourceName){
		finalPath += resourceName + "/";
	}
	
	return finalPath;
}

buildUtil.makeResourceUri = function(resourceName, templatePath, srcRoot, prefixes){
	var bestPrefix = "";
	var bestPrefixPath = "";
	if(prefixes){
		for (var i = 0; i < prefixes.length; i++){
			var prefix = prefixes[i];
			//Prefix must match from the start of the resourceName string.
			if(resourceName.indexOf(prefix[0]) == 0){
				if(prefix[0].length > bestPrefix.length){
					bestPrefix = prefix[0];
					bestPrefixPath = prefix[1];
				}
			}
		}

		if(bestPrefixPath != ""){
			//Convert resourceName to a path
			resourceName = resourceName.replace(bestPrefix, "");
			if(resourceName.indexOf(".") == 0){
				resourceName = resourceName.substring(1, resourceName.length);
			}
			resourceName = resourceName.replace(/\./g, "/");

			//Final path construction
			var finalPath = bestPrefixPath + "/";
			if(resourceName){
				finalPath += resourceName + "/";
			}
			finalPath += templatePath;

			return finalPath;
		}
	}

	return srcRoot + templatePath;
}

buildUtil.internTemplateStrings = function(/*Object*/dependencies, /*String*/srcRoot, /*RegExp*/optimizeIgnoreRegExp){
	//summary: interns strings in files for all .js files in the srcRoot directory.
	var prefixes = dependencies["prefixes"] || [];
	var skiplist = dependencies["internSkipList"] || [];

	//Intern strings for all files in widget dir (xdomain and regular files)
	var fileList = fileUtil.getFilteredFileList(srcRoot, /\.js$/, true);
	if(fileList){
		for(var i = 0; i < fileList.length; i++){
			//Skip nls directories.
			var fileName = fileList[i];
			if(!fileName.match(/\/nls\//) && !fileName.match(optimizeIgnoreRegExp)){
				buildUtil.internTemplateStringsInFile(fileList[i], srcRoot, prefixes, skiplist);
			}
		}
	}
}

buildUtil.internTemplateStringsInFile = function(resourceFile, srcRoot, prefixes, skiplist){
	var resourceContent = fileUtil.readFile(resourceFile);
	resourceContent = buildUtil.interningRegexpMagic(resourceFile, resourceContent, srcRoot, prefixes, skiplist);
	fileUtil.saveUtf8File(resourceFile, resourceContent);
}

buildUtil.interningRegexpMagic = function(resourceFile, resourceContent, srcRoot, prefixes, skiplist){
	var shownFileName = false;
	return resourceContent.replace(buildUtil.interningGlobalDojoUriRegExp, function(matchString){
		var parts = matchString.match(buildUtil.interningLocalDojoUriRegExp);

		var filePath = "";
		var resourceNsName = "";

		if(!shownFileName){
			logger.trace("Interning strings for : " + resourceFile);
			shownFileName = true;
		}

		//logger.trace("Module match: " + parts[6] + " and " + parts[9]);
		filePath = buildUtil.makeResourceUri(parts[6], parts[9], srcRoot, prefixes);
		resourceNsName = parts[6] + ':' + parts[9];		

		if(!filePath || buildUtil.isValueInArray(resourceNsName, skiplist)){
			logger.trace("    skipping " + filePath);
		}else{
			logger.trace("    " + filePath);
			//buildUtil.jsEscape will add starting and ending double-quotes.
			var jsEscapedContent = buildUtil.jsEscape(fileUtil.readFile(filePath));
			if(jsEscapedContent){
				if(matchString.indexOf("dojo.uri.cache.allow") != -1){
					//Handle dojo.uri.cache-related interning.
					var parenIndex = matchString.lastIndexOf(")");
					matchString = matchString.substring(0, parenIndex + 1) + ", " + jsEscapedContent;
					matchString = matchString.replace("dojo.uri.cache.allow", "dojo.uri.cache.set");
				}else{
					//Handle templatePath/templateCssPath-related interning.
					if(parts[3] == "templatePath"){
						//Replace templatePaths
						matchString = "templateString" + parts[4] + jsEscapedContent;
					}else{
						//Dealing with templateCssPath
						//For the CSS we need to keep the template path in there
						//since the widget loading stuff uses the template path to
						//know whether the CSS has been processed yet.
						//Could have matched assignment via : or =. Need different statement separators at the end.
						var assignSeparator = parts[4];
						var statementSeparator = ",";
						var statementPrefix = "";
			
						//FIXME: this is a little weak because it assumes a "this" in front of the templateCssPath
						//when it is assigned using an "=", as in 'this.templateCssPath = dojo.uri.dojoUri("some/path/to/Css.css");'
						//In theory it could be something else, but in practice it is not, and it gets a little too weird
						//to figure out, at least for now.
						if(assignSeparator == "="){
							statementSeparator = ";";
							statementPrefix = "this.";
						}
						matchString = "templateCssString" + assignSeparator + jsEscapedContent + statementSeparator + statementPrefix + parts[0];
					}
				}
			}
		}

		return matchString;
	});
}

buildUtil.regExpEscape = function(/*String*/value){
	//summary: Makes sure regexp-sensitive characters in a string are escaped correctly.
	return value.replace(/([\.\*\/])/g, "\\$1");
}

buildUtil.jsEscape = function(/*string*/str){
//summary:
//	Adds escape sequences for non-visual characters, double quote and backslash
//	and surrounds with double quotes to form a valid string literal.
//	Take from the old dojo.string.escapeString code.
//	Include it here so we don't have to load dojo.
	return ('"' + str.replace(/(["\\])/g, '\\$1') + '"'
		).replace(/[\f]/g, "\\f"
		).replace(/[\b]/g, "\\b"
		).replace(/[\n]/g, "\\n"
		).replace(/[\t]/g, "\\t"
		).replace(/[\r]/g, "\\r"); // string
}

buildUtil.isValueInArray = function(/*Object*/value, /*Array*/ary){
	//summary: sees if value is in the ary array. Uses == to see if the
	//array item matches value.
	for(var i = 0; i < ary.length; i++){
		if(ary[i] == value){
			return true; //boolean
		}
	}
	return false; //boolean
}

buildUtil.convertArrayToObject = function(/*Array*/ary){
	//summary: converts an array that has String members of "name=value"
	//into an object, where the properties on the object are the names in the array
	//member name/value pairs.
	var result = {};
	for(var i = 0; i < ary.length; i++){
		var separatorIndex = ary[i].indexOf("=");
		if(separatorIndex == -1){
			throw "Malformed name/value pair: [" + ary[i] + "]. Format should be name=value";
		}
		result[ary[i].substring(0, separatorIndex)] = ary[i].substring(separatorIndex + 1, ary[i].length);
	}
	return result; //Object
}

buildUtil.optimizeJs = function(/*String fileName*/fileName, /*String*/fileContents, /*String*/copyright, /*String*/optimizeType){
	//summary: either strips comments from string or compresses it.
	copyright = copyright || "";

	//Use rhino to help do minifying/compressing.
	//Even when using Dean Edwards' Packer, run it through the custom rhino so
	//that the source is formatted nicely for Packer's consumption (in particular get
	//commas after function definitions).
	var context = Packages.org.mozilla.javascript.Context.enter();
	try{
		// Use the interpreter for interactive input (copied this from Main rhino class).
		context.setOptimizationLevel(-1);

		var script = context.compileString(fileContents, fileName, 1, null);
		if(optimizeType.indexOf("shrinksafe") == 0){
			//Apply compression using custom compression call in Dojo-modified rhino.
			fileContents = new String(context.compressScript(script, 0, fileContents, 1));
			if(optimizeType.indexOf(".keepLines") == -1){
				fileContents = fileContents.replace(/[\r\n]/g, "");
			}
		}else if(optimizeType == "comments" || optimizeType == "packer"){
			//Strip comments
			fileContents = new String(context.decompileScript(script, 0));
			
			if(optimizeType == "packer"){
				buildUtil.setupPacker();

				// var base62 = false;
				// var shrink = true;
				var base62 = true;
				var shrink = true;
				var packer = new Packer();
				fileContents = packer.pack(fileContents, base62, shrink);
			}else{
				//Replace the spaces with tabs.
				//Ideally do this in the pretty printer rhino code.
				fileContents = fileContents.replace(/    /g, "\t");
			}

			//If this is an nls bundle, make sure it does not end in a ;
			//Otherwise, bad things happen.
			if(fileName.match(/\/nls\//)){
				fileContents = fileContents.replace(/;\s*$/, "");
			}
		}
	}finally{
		Packages.org.mozilla.javascript.Context.exit();
	}


	return copyright + fileContents;
}


buildUtil.setupPacker = function(){
	//summary: loads the files needed to run Dean Edwards' Packer.
	if(typeof(Packer) == "undefined"){
		load("jslib/packer/base2.js");
		load("jslib/packer/Packer.js");
		load("jslib/packer/Words.js");

	}
}

buildUtil.stripComments = function(/*String*/startDir, /*RegeExp*/optimizeIgnoreRegExp, /*String*/copyrightText, /*String*/optimizeType){
	//summary: strips the JS comments from all the files in "startDir", and all subdirectories.
	var copyright = (copyrightText || fileUtil.readFile("copyright.txt")) + fileUtil.getLineSeparator();
	var fileList = fileUtil.getFilteredFileList(startDir, /\.js$/, true);
	if(fileList){
		for(var i = 0; i < fileList.length; i++){
			//Don't process dojo.js since it has already been processed.
			//Don't process dojo.js.uncompressed.js because it is huge.
			//Don't process anything that might be in a buildscripts folder (only a concern for webbuild.sh)
			if(!fileList[i].match(optimizeIgnoreRegExp)
				&& !fileList[i].match(/buildscripts/)
				&& !fileList[i].match(/nls/)
				&& !fileList[i].match(/tests\//)){
				logger.trace("Optimizing (" + optimizeType + ") file: " + fileList[i]);
				
				//Read in the file. Make sure we have a JS string.
				var fileContents = fileUtil.readFile(fileList[i]);

				//Do comment removal.
				try{
					fileContents = buildUtil.optimizeJs(fileList[i], fileContents, copyright, optimizeType);
				}catch(e){
					logger.error("Could not strip comments for file: " + fileList[i] + ", error: " + e);
				}

				//Write out the file with appropriate copyright.
				fileUtil.saveUtf8File(fileList[i], fileContents);
			}
		}
	}
}

buildUtil.optimizeCss = function(/*String*/startDir, /*String*/optimizeType, /*String?*/cssImportIgnore){
	//summmary: Optimizes CSS files in a directory.
	
	if(optimizeType.indexOf("comments") != -1){
		//Make sure we have a delimited ignore list to make matching faster
		if(cssImportIgnore){
			cssImportIgnore = cssImportIgnore + ",";
		}

		var fileList = fileUtil.getFilteredFileList(startDir, /\.css$/, true);
		if(fileList){
			for(var i = 0; i < fileList.length; i++){
				var fileName = fileList[i];
				logger.trace("Optimizing (" + optimizeType + ") CSS file: " + fileName);
				
				//Read in the file. Make sure we have a JS string.
				var originalFileContents = fileUtil.readFile(fileName);
				var fileContents = buildUtil.flattenCss(fileName, originalFileContents, cssImportIgnore);

				//Do comment removal.
				try{
					var startIndex = -1;
					//Get rid of comments.
					while((startIndex = fileContents.indexOf("/*")) != -1){
						var endIndex = fileContents.indexOf("*/", startIndex + 2);
						if(endIndex == -1){
							throw "Improper comment in CSS file: " + fileName;
						}
						fileContents = fileContents.substring(0, startIndex) + fileContents.substring(endIndex + 2, fileContents.length);
					}
					//Get rid of newlines.
					if(optimizeType.indexOf(".keepLines") == -1){
						fileContents = fileContents.replace(/[\r\n]/g, "");
						fileContents = fileContents.replace(/\s+/g, " ");
						fileContents = fileContents.replace(/\{\s/g, "{");
						fileContents = fileContents.replace(/\s\}/g, "}");
					}else{
						//Remove multiple empty lines.
						fileContents = fileContents.replace(/(\r\n)+/g, "\r\n");
						fileContents = fileContents.replace(/(\n)+/g, "\n");
					}
				}catch(e){
					fileContents = originalFileContents;
					logger.error("Could not optimized CSS file: " + fileName + ", error: " + e);
				}
	
				//Write out the file with appropriate copyright.
				fileUtil.saveUtf8File(fileName + ".commented.css", originalFileContents);
				fileUtil.saveUtf8File(fileName, fileContents);
			}
		}
	}
}

buildUtil.backSlashRegExp = /\\/g;
buildUtil.cssImportRegExp = /\@import\s+(url\()?\s*([^);]+)\s*(\))?([\w, ]*)(;)?/g;
buildUtil.cssUrlRegExp = /\url\(\s*([^\)]+)\s*\)?/g;

buildUtil.cleanCssUrlQuotes = function(/*String*/url){
	//summary: If an URL from a CSS url value contains start/end quotes, remove them.
	//This is not done in the regexp, since my regexp fu is not that strong,
	//and the CSS spec allows for ' and " in the URL if they are backslash escaped.

	//Make sure we are not ending in whitespace.
	//Not very confident of the css regexps above that there will not be ending
	//whitespace.
	url = url.replace(/\s+$/, "");

	if(url.charAt(0) == "'" || url.charAt(0) == "\""){
		url = url.substring(1, url.length - 1);
	}

	return url;
}

buildUtil.flattenCss = function(/*String*/fileName, /*String*/fileContents, /*String?*/cssImportIgnore){
	//summary: inlines nested stylesheets that have @import calls in them.

	//Find the last slash in the name.
	fileName = fileName.replace(buildUtil.backSlashRegExp, "/");
	var endIndex = fileName.lastIndexOf("/");

	//Make a file path based on the last slash.
	//If no slash, so must be just a file name. Use empty string then.
	var filePath = (endIndex != -1) ? fileName.substring(0, endIndex + 1) : "";

	return fileContents.replace(buildUtil.cssImportRegExp, function(fullMatch, urlStart, importFileName, urlEnd, mediaTypes){
		//Only process media type "all" or empty media type rules.
		if(mediaTypes && ((mediaTypes.replace(/^\s\s*/, '').replace(/\s\s*$/, '')) != "all")){
			return fullMatch;
		}

		importFileName = buildUtil.cleanCssUrlQuotes(importFileName);
		
		//Ignore the file import if it is part of an ignore list.
		if(cssImportIgnore && cssImportIgnore.indexOf(importFileName + ",") != -1){
			return fullMatch;
		}

		//Make sure we have a unix path for the rest of the operation.
		importFileName = importFileName.replace(buildUtil.backSlashRegExp, "/");

		try{
			//if a relative path, then tack on the filePath.
			//If it is not a relative path, then the readFile below will fail,
			//and we will just skip that import.
			var fullImportFileName = importFileName.charAt(0) == "/" ? importFileName : filePath + importFileName;
			var importContents = fileUtil.readFile(fullImportFileName);

			//Make sure to flatten any nested imports.
			importContents = buildUtil.flattenCss(fullImportFileName, importContents);
			
			//Make the full import path
			var importEndIndex = importFileName.lastIndexOf("/");

			//Make a file path based on the last slash.
			//If no slash, so must be just a file name. Use empty string then.
			var importPath = (importEndIndex != -1) ? importFileName.substring(0, importEndIndex + 1) : "";

			//Modify URL paths to match the path represented by this file.
			importContents = importContents.replace(buildUtil.cssUrlRegExp, function(fullMatch, urlMatch){
				var fixedUrlMatch = buildUtil.cleanCssUrlQuotes(urlMatch);
				fixedUrlMatch = fixedUrlMatch.replace(buildUtil.backSlashRegExp, "/");
				if(fixedUrlMatch.charAt(0) != "/"){
					//It is a relative URL, tack on the path prefix
					urlMatch = importPath + fixedUrlMatch;
				}else{
					logger.trace(importFileName + "\n  URL not a relative URL, skipping: " + urlMatch);
				}

				//Collapse .. and .
				var parts = urlMatch.split("/");
				for(var i = parts.length - 1; i > 0; i--){
					if(parts[i] == "."){
						parts.splice(i, 1);
					}else if(parts[i] == ".."){
						if(i != 0 && parts[i - 1] != ".."){
							parts.splice(i - 1, 2);
							i -= 1;
						}
					}
				}

				return "url(" + parts.join("/") + ")";
			});

			return importContents;
		}catch(e){
			logger.trace(fileName + "\n  Cannot inline css import, skipping: " + importFileName);
			return fullMatch;
		}
	});
}

buildUtil.guardProvideRegExp = /dojo\.provide\(([\'\"][^\'\"]*[\'\"])\)/;

buildUtil.addGuards = function(/*String || Array*/startDir){
	//summary: adds a definition guard around code in a file to protect
	//against redefinition cases when layered builds are used. Accepts a string
	//of the start directory to use, or an array of file name strings to process.
	var lineSeparator = fileUtil.getLineSeparator();

	var fileList = startDir;
	if(fileList instanceof String){
		fileList = fileUtil.getFilteredFileList(fileList, /\.js$/, true);
	}else{
		//Make sure we only process .js files
		for(var i = fileList.length - 1; i >= 0; i--){
			if(!fileList[i].match(/\.js$/)){
				fileList.splice(i, 1);
			}
		}
	}

	if(fileList){
		for(var i = 0; i < fileList.length; i++){
			var fileContents = fileUtil.readFile(fileList[i]);
			buildUtil.guardProvideRegExp.lastIndex = 0;
			var match = buildUtil.guardProvideRegExp.exec(fileContents);
			if(match){
				//Only add the guard if there is not already one in the file.
				var existingGuardRegExp = new RegExp('if\\(\\!dojo\\._hasResource\\[' + match[1] + '\\]\\)');
				if(!fileContents.match(existingGuardRegExp)){
					fileContents = 'if(!dojo._hasResource[' + match[1] + ']){ //_hasResource checks added by build. Do not use _hasResource directly in your code.'
						+ lineSeparator
						+ 'dojo._hasResource[' + match[1] + '] = true;'
						+ lineSeparator
						+ fileContents
						+ lineSeparator
						+ '}'
						+ lineSeparator;
	
					fileUtil.saveUtf8File(fileList[i], fileContents);
				}
			}
		}
	}
}

buildUtil.processConditionalsForDir = function(/*String*/startDir, /*RegExp*/layerIgnoreRegExp, /*Object*/kwArgs){
	//summary: processes build conditionals for a directory, but ignores files in the layerIgnoreRegExp argument.
	var fileList = fileUtil.getFilteredFileList(startDir, /\.js$/, true);
	if(fileList){
		for(var i = 0; i < fileList.length; i++){
			//Skip nls directories.
			var fileName = fileList[i];
			if(!fileName.match(layerIgnoreRegExp)){
				var fileContents = fileUtil.readFile(fileName);
				if(fileContents.indexOf("//>>") != -1){
					fileUtil.saveFile(fileName, buildUtil.processConditionals(fileName, fileContents, kwArgs));
				}
			}
		}
	}
}

buildUtil.conditionalRegExp = /(exclude|include)Start\s*\(\s*["'](\w+)["']\s*,(.*)\)/;
buildUtil.processConditionals = function(/*String*/fileName, /*String*/fileContents, /*Object*/kwArgs){
	//summary: processes the fileContents for some Dojo-specific conditional comments.
	var foundIndex = -1;
	var startIndex = 0;
	
	while((foundIndex = fileContents.indexOf("//>>", startIndex)) != -1){
		//Found a conditional. Get the conditional line.
		var lineEndIndex = fileContents.indexOf("\n", foundIndex);
		if(lineEndIndex == -1){
			lineEndIndex = fileContents.length - 1;
		}

		//Increment startIndex past the line so the next conditional search can be done.
		startIndex = lineEndIndex + 1;

		//Break apart the conditional.
		var conditionLine = fileContents.substring(foundIndex, lineEndIndex + 1);
		var matches = conditionLine.match(buildUtil.conditionalRegExp);
		if(matches){
			var type = matches[1];
			var marker = matches[2];
			var condition = matches[3];
			var isTrue = false;
			//See if the condition is true.
			try{
				isTrue = !!eval("(" + condition + ")");
			}catch(e){
				throw "Error in file: "
					+ fileName
					+ ". Conditional comment: "
					+ conditionLine
					+ " failed with this error: " + e;
			}
		
			//Find the endpoint marker.
			var endRegExp = new RegExp('\\/\\/\\>\\>\\s*' + type + 'End\\(\\s*[\'"]' + marker + '[\'"]\\s*\\)', "g");
			var endMatches = endRegExp.exec(fileContents.substring(startIndex, fileContents.length));
			if(endMatches){
				
				var endMarkerIndex = startIndex + endRegExp.lastIndex - endMatches[0].length;
				
				//Find the next line return based on the match position.
				lineEndIndex = fileContents.indexOf("\n", endMarkerIndex);
				if(lineEndIndex == -1){
					lineEndIndex = fileContents.length - 1;
				}

				//Should we include the segment?
				var shouldInclude = ((type == "exclude" && !isTrue) || (type == "include" && isTrue));
				
				//Remove the conditional comments, and optionally remove the content inside
				//the conditional comments.
				var startLength = startIndex - foundIndex;
				fileContents = fileContents.substring(0, foundIndex)
					+ (shouldInclude ? fileContents.substring(startIndex, endMarkerIndex) : "")
					+ fileContents.substring(lineEndIndex + 1, fileContents.length);
				
				//Move startIndex to foundIndex, since that is the new position in the file
				//where we need to look for more conditionals in the next while loop pass.
				startIndex = foundIndex;
			}else{
				throw "Error in file: "
					+ fileName
					+ ". Cannot find end marker for conditional comment: "
					+ conditionLine;
				
			}
		}
	}

	return fileContents;
}

buildUtil.setScopeDjConfig = function(/*String*/fileContents, /*String*/djConfigString){
	//summary: burns in a local djConfig for the file contents.
	//djConfigString should be a string.
	//Have to use eval to avoid name condensing by shrinksafe.
	return fileContents.replace(/\/\*\*Build will replace this comment with a scoped djConfig \*\*\//, 'eval("var djConfig = ' + djConfigString.replace(/(['"])/g, '\\$1') + ';");');
}

buildUtil.setScopeNames = function(/*String*/fileContents, /*String*/scopeMap){
	//summary: burns in the scope names into the file contents.
	//scopeMap should be a [["name","value"],["name","value"]] string. Notice the lack of spaces.
	//Single quotes can be used instead of double quotes.
	return fileContents.replace(/var\s+sMap\s+=\s+null/, "var sMap = " + scopeMap);
}

buildUtil.symctr = 0;
buildUtil.symtbl = null;
buildUtil.generateSym = function(/*String*/name){
	var m = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
	var len = m.length;
	var s;
	if(buildUtil.symctr < len*len){
		s = m.charAt(Math.floor(buildUtil.symctr/len))
			+m.charAt(buildUtil.symctr%len);
	}else{
		s = m.charAt(Math.floor(buildUtil.symctr/(len*len))-1)
			+m.charAt(Math.floor(buildUtil.symctr/len)%len)
			+m.charAt(buildUtil.symctr%len);
	}
	s = "$D" + s;
	buildUtil.symctr++;
	var ret;
	if(kwArgs.symbol == "long"){
		ret = name; // + "_" + s;
	}else if(kwArgs.symbol == "short"){
		buildUtil.symtbl[s + "_"] = name;
		ret = s + "_";
	}
	return ret;
}

buildUtil.insertSymbols = function(/*String*/startDir, /*Object*/kwArgs){
	//summary: add global function symbols to anonymous functions.
	buildUtil.symtbl = {};
	var fileList = fileUtil.getFilteredFileList(startDir, /\.js$/, true);
	if(fileList){
		logger.trace("Inserting global function symbols in: "+startDir);
		for(var i = 0; i < fileList.length; i++){
			//Don't process loader_debug.js since global symbols conflict with loader.js.
			//Don't process dojo.js.uncompressed.js because it is huge.
			//Don't process anything that might be in a buildscripts folder (only a concern for webbuild.sh)
			if(!fileList[i].match(/loader_debug\.js/)
				&& !fileList[i].match(/\.uncompressed\.js/)
				&& !fileList[i].match(/buildscripts/)
				&& !fileList[i].match(/nls/)
				&& !fileList[i].match(/tests\//)){
				
				//Read in the file. Make sure we have a JS string.
				var fileContents = fileUtil.readFile(fileList[i]);

				//Do insertion.
				var className;
				if(fileContents.match(/dojo\.provide\("(.*)"\);/)){
					className = RegExp.$1.replace(/\./g, "_")+"_";
				}
				if(className){
					fileContents = fileContents.replace(/^(\s*)(\w+)(\s*:\s*function)\s*(\(.*)$/mg, function(str, p1, p2, p3, p4){
						return p1+p2+p3+" "+buildUtil.generateSym(className+p2)+p4;
					});
					fileContents = fileContents.replace(/^(\s*this\.)(\w+)(\s*=\s*function)\s*(\(.*)$/mg, function(str, p1, p2, p3, p4){
						return p1+p2+p3+" "+buildUtil.generateSym(className+p2)+p4;
					});
				}
				fileContents = fileContents.replace(/^(\s*)([\w\.]+)(\s*=\s*function)\s*(\(.*)/mg, function(str, p1, p2, p3, p4){
					return p1+p2+p3+" "+buildUtil.generateSym(p2.replace(/\./g, "_"))+p4;
				});

				//Write out the file
				fileUtil.saveUtf8File(fileList[i], fileContents);
			}
		}

		if(kwArgs.symbol == "short"){
			var symbolText = "";
			var lineSeparator = fileUtil.getLineSeparator();
			for(var key in buildUtil.symtbl){
				symbolText += key + ": \"" + buildUtil.symtbl[key] + "\"" + lineSeparator;
			}
			fileUtil.saveFile(startDir + "/symboltable.txt", symbolText);
		}
	}
}
