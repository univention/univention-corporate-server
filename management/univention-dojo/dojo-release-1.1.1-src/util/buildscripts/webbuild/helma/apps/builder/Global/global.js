
function load(/*String*/fileName){
	//summary: opens the file at fileName and evals the contents as JavaScript.
	
	//Read the file
	var fileContents = readFile(fileName);

	//Eval the contents.
	var Context = Packages.org.mozilla.javascript.Context;
	var context = Context.enter();
	try{
		return context.evaluateString(global, fileContents, fileName, 1, null);
	}finally{
		Context.exit();
	}
}

function readFile(/*String*/path, /*String?*/encoding){
	//summary: reads a file and returns a string
	encoding = encoding || "utf-8";
	var file = new File(path);
	var lineSeparator = "\n";
	var input = new java.io.BufferedReader(new java.io.InputStreamReader(new java.io.FileInputStream(file), encoding));
	try {
		var stringBuffer = new java.lang.StringBuffer();
		var line = "";
		while((line = input.readLine()) !== null){
			stringBuffer.append(line);
			stringBuffer.append(lineSeparator);
		}
		//Make sure we return a JavaScript string and not a Java string.
		return new String(stringBuffer.toString()); //String
	} finally {
		input.close();
	}
}
