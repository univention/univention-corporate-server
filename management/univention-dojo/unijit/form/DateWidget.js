dojo.provide("unijit.form.DateWidget");
dojo.require("dijit.form.DateTextBox");
dojo.declare('unijit.form.DateWidget', dijit.form.DateTextBox,
{
//templatePath : dojo.moduleUrl("unijit", "form/template/DateWidget.html"),
//#extended template string from dojo/dijit/form/ValidationTextBox.js included here directly:
templateString:"<div class=\"dijit dijitReset dijitInlineTable dijitLeft\"\n\tid=\"widget_${id}\"\n\tdojoAttachEvent=\"onmouseenter:_onMouse,onmouseleave:_onMouse,onmousedown:_onMouse\" waiRole=\"presentation\"\n\t><div style=\"overflow:hidden;\"\n\t\t><span class=\"dijitReset dijitCalendarIcon\" dojoAttachEvent=\"onclick:_open\"></span\n\t\t><div class=\"dijitReset dijitValidationIcon\"><br></div\n\t\t><div class=\"dijitReset dijitValidationIconText\">&Chi;</div\n\t\t><div class=\"dijitReset dijitInputField\"\n\t\t\t><input class=\"dijitReset\" dojoAttachPoint='textbox,focusNode' dojoAttachEvent='onfocus:_update,onkeyup:_onkeyup,onblur:_onMouse,onkeypress:_onKeyPress' autocomplete=\"off\"\n\t\t\ttype='${type}' name='${name}'\n\t\t/></div\n\t></div\n></div>\n",


                _onFocus: function(/*Event*/ evt){
                        // summary: don't open the TimePicker popup onFocus, open it via dijitCalendarIcon onclick
                }

});
