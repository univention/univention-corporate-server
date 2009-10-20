dependencies = {
	layers: [
		{
			name: "../unijit/unijit.js", // copyrightFile: "../unijit/Copyright",
			layerDependencies: [
			],
			dependencies: [
				"dijit.form.CheckBox",
				"dijit.form.ComboBox",
				"dijit.form.FilteringSelect",
				"dijit.form.MultiSelect",
				"dijit.form.SimpleTextarea",
				"dijit.form.TextBox",
				"dijit.form.ValidationTextBox",
				"dijit.layout.ContentPane",
				"dijit.layout.StackContainer",
				"dojo.parser",
				"unijit.form.DateWidget", // "dojo.cldr.nls.gregorian"
			]
		}
	],

	prefixes: [
		[ "dijit", "../dijit" ],
		[ "dojox", "../dojox" ],
		[ "unijit", "../../unijit" ]
	]
}
