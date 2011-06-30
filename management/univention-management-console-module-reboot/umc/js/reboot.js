/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.reboot");

dojo.require("dijit.layout.BorderContainer");
dojo.require("umc.i18n");
dojo.require("umc.widgets.Module");

dojo.declare("umc.modules.reboot", [ umc.widgets.Module, umc.i18n.Mixin ], {

	// generate border layout and add it to the module
	this._layoutContainer = new dijit.layout.BorderContainer({});
	this.addChild(this._layoutContainer);

	buildRendering: function() {
		// call superclass method
		this.inherited(arguments);

		// generate border layout and add it to the module
		this._layoutContainer = new dijit.layout.BorderContainer({});
		this.addChild(this._layoutContainer);


        var widgets = [{
		    type: 'ComboBox',
		    name: 'action',
            // FIXME
		    // value: 'all',
		    // description: this._( 'Category the UCR variable should associated with' ),
		    label: this._('Action'),
		    staticValues: [
                { id: 'reboot', label: this._('Reboot') }
                { id: 'halt', label: this._('Stop') }
            ]
        },{
		    type: 'TextBox',
		    name: 'message',
            // TODO
            // value = '' ?
		    // value: '',
		    // description: this._( 'Keyword that should be searched for in the selected attribute' ),
		    label: this._('Reason for this reboot/shutdown')
        }];

	    var buttons = [{
		    name: 'execute',
		    label: this._( 'Execute' ),
		    callback: dojo.hitch(this, function() {
			    this._form.save();
			    this.hide();
		    })
	    }];



}
