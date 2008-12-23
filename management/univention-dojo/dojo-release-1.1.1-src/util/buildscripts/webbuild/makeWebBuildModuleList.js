//This file generates a list of modules that can be used in a web build.
//This file should be called from ant/command line, and the output file
//needs to be generated before the web build will work.


function buildTreeData(/*Object*/obj, /*String*/nodeName){
	//summary: makes a TreeV3-friendly data structure.
	
	var childNames = [];
	if(obj["dojoModuleName"]){
		var result = { title: nodeName, dojoModuleName: obj["dojoModuleName"]};
	}else{
		var result = {};
	}
	
	//Working with a branch.
	for(var childName in obj){
		if(childName != "dojoModuleName"){
			childNames.push(childName);
		}
	}
	childNames = childNames.sort();
	if(childNames.length > 0){
		result.children = [];
		var result = { title: nodeName, children: []};
		for(var i = 0; i < childNames.length; i++){
			result.children.push(buildTreeData(obj[childNames[i]], childNames[i]));
		}
	}
	return result;
}


//START of the "main" part of the script.
//This is the entry point for this script file.
var srcRoot = arguments[0];
var outputFileName = arguments[1];

//Load Dojo so we can reuse code.
djConfig={
	baseRelativePath: "../../"
};
load('../../dojo.js');
dojo.require("dojo.json");

load("../fileUtil.js");
load("../buildUtil.js");

//Get a list of files that might be modules.
var fileList = fileUtil.getFilteredFileList(srcRoot, /\.js$/, true);

var provideRegExp = /dojo\.provide\(\".*\"\)/g;

//Search the modules for a matching dojo.provide() call.
//Need to do this because some files (like nls/*.js files) are
//not really modules.
var provideList = [];
for(var i = 0; i < fileList.length; i++){
	var fileName = fileList[i];
	var fileContents = new fileUtil.readFile(fileName);

	var matches = fileContents.match(provideRegExp);
	if(matches){
		for(var j = 0; j < matches.length; j++){
			//strip off the .js file extension, and convert __package__ names to *
			var modFileName = fileName.substring(0, fileName.length - 3).replace(/__package__/g, "*");
			var provideName = matches[j].substring(matches[j].indexOf('"') + 1, matches[j].lastIndexOf('"'));
			//Strip off leading dojo. This means this only works for Dojo code.
			var modProvideName = provideName.replace(/^dojo\./, "");

			if (modFileName.lastIndexOf(modProvideName.replace(/\./g, "/")) == modFileName.length - modProvideName.length){
				provideList.push(provideName);
				break;
			}
		}
	
	}
}

provideList = provideList.sort();

//Create the object that represents the module structures.
var moduleHolder = {};

for(var i = 0; i < provideList.length; i++){
	var moduleObject = dojo.parseObjPath(provideList[i], moduleHolder, true);
	moduleObject.obj[moduleObject.prop] = {dojoModuleName: provideList[i] };
}

//Transform the object into something appropriate for a tree control.
var treeData = buildTreeData(moduleHolder, "Dojo Modules");

//Output the results.
fileUtil.saveFile(outputFileName, "var treeData = " + dojo.json.serialize(treeData) + ";");

