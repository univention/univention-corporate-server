//************************************************************************
//DO NOT dojo.require() any modules in this file or the page that uses this
//file. It means those modules will be excluded from the build if you do so.
//************************************************************************


//Define some methods that are defined in Rhino, but we need web equivalents
//in order for the build scripts to work.
fileUtil.readFile = readText = readFile = function(uri){
	return dojo.hostenv.getText(uri);
}

load = function(uri){
	eval(readFile(uri));
}

//Define some overrides for the buildUtil functions.
fileUtil.getLineSeparator = function(){
	//summary: Gives the line separator for the platform.
	//For web builds override this function.
	return "\n";
}

buildUtil.getDojoLoader = function(/*Object?*/dependencies){
	//summary: gets the type of Dojo loader for the build. For example default or
	//xdomain loading. Override for web builds.
	return dependencies["loader"];
}

//Define the webbuild object.
webbuild = {
	build: function(/*String*/depString, /*String*/version, /*String*/xdDojoPath){
		depString = depString.replace(/^\s*/, "").replace(/\s*$/, "");

		var dependencies;
		eval("dependencies = [" + depString + "];");
		dependencies.loader = "xdomain";
		
		var dependencyResult = buildUtil.getDependencyList(dependencies, null, true);
		
		if(location.toString().indexOf("file:") == 0){
			//Return the dojo contents
			webbuild.dojoContents = "Just a test. Run the build with a web server that runs PHP to get a real build file.";

			var outputWindow = window.open("webbuild/dojo.js.html", "dojoOutput");
			outputWindow.focus();
		}else{
			parent.sendDependencyResultToServer(dependencyResult);
		}
	},

	getDojoContents: function(){
		return webbuild.dojoContents;
	}
}
