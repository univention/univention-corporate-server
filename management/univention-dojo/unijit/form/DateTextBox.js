dojo.provide("unijit.form.DateTextBox");

dojo.require("dijit._Calendar");
dojo.require("dijit.form.DateTextBox");

dojo.declare(
	"unijit.form.DateTextBox",
	dijit.form.DateTextBox,
	{
		templatePath : dojo.moduleUrl("unijit", "form/template/DateTextBox.html"),
	}
);

