/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.sysinfo");

dojo.require("umc.i18n");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Wizard");

dojo.declare("umc.modules.sysinfo", [ umc.widgets.Module, umc.i18n.Mixin ], {

	_wizard: null,

	buildRendering: function() {
		this.inherited(arguments);

		this._wizard = new umc.widgets.Wizard({
			pages: [{
				name: 'general',
				headerText: this._('General Information'),
				helpText: this._(''),
				widgets: [{
					type: 'Text',
					name: 'firstText',
					content: this._('This module collects information about the hardware of your system. This might be helpful in connection with a support case. By transmitting the data to Univention you provide the information on which platforms UCS is currently used and therefore should be supported by newer versions. All information gathered by this module will be made anonymous before the transfer to Univention. In the following procedure you will be informed in detail about the each step.<br /><br />No information is transmitted without your acceptance!') + '<br /><br />'
				}, {
					type: 'TextBox',
					name: 'manufacturer',
					label: this._('Manufacturer')
				}, {
					type: 'TextBox',
					name: 'model',
					label: this._('Model')
				}, {
					type: 'TextBox',
					name: 'comment',
					label: this._('Descriptive comment')
				}, {
					type: 'CheckBox',
					name: 'supportBox',
					label: this._('This is related to a support case')
				}, {
					type: 'Text',
					name: 'secondText',
					label: this._('If this is related to a support case the next step will be to enter the ticket number. if not than the information about your system will be collected and a summary is shown.')
				}],
				layout: [['firstText'],
						 ['manufacturer', 'model'],
						 ['comment', 'supportBox'],
						 ['secondText']]
			}, {
				name: 'support',
				headerText: this._('Support Information'),
				helpText: this._(''),
				widgets: [{
					type: 'Text',
					name: 'firstText',
					content: this._('If a Univention Support Engineer has asked you to provide these information, than please insert the ticket number of the related support ticket into the following text field. The ticket number can be found in the subject of a support mail of the ticket. This information will speed up the processing of the ticket.') + '<br /><br />'
				}, {
					type: 'TextBox',
					name: 'ticket',
					label: this._('This is related to a support case'),
					value: ''
				}, {
					type: 'Text',
					name: 'secondText',
					content: this._('In the next step the information about the hardware of your system will be collect and a summary will be shown. No information will be send to Univention.') + '<br /><br />'
				}],
				layout: [['firstText'],
						 ['ticket'],
						 ['secondText']]
			}, {
				name: 'collect',
				headerText: this._('Collected Data'),
				helpText: this._(''),
				widgets: [{
					type: 'Text',
					name: 'firstText',
					content: this._('The following information has been collected and will be transfered to Univention with your acceptance.') + '<br /><br />'
				}, {
					type: 'TextBox',
					name: 'cpu',
					label: this._('CPU'),
					value: ''
				}, {
					type: 'TextBox',
					name: 'cores', // TODO: rename?
					label: this._('Number of CPUs'),
					value: ''
				}, {
					type: 'TextBox',
					name: 'memory',
					label: this._('Memory'),
					value: ''
				}, {
					type: 'TextBox',
					name: 'network',
					label: this._('Network Device'),
					value: ''
				}, {
					type: 'TextBox',
					name: 'graphic',
					label: this._('Graphics Device')
				}, {
					type: 'Text',
					name: 'secondText',
					content: this._('Additionally to the information listed above some more details about your system has been collected. The hole set of collected data that will be transmitted to Univention can be downloaded at the following URL:') + '<br /><br />'
				}, {
					type: 'Text',
					name: 'thirdText',
					content: this._('In the following step two possibilities to transmit the information to Univention will be described.')
				}],
				buttons: [{
					name: 'download',
					label: this._('Archive with system information')
				}],
				layout: [['firstText'],
						 ['cpu'],
						 ['cores'],
						 ['memory'],
						 ['network'],
						 ['graphic'],
						 ['secondText'],
						 ['download'],
						 ['thirdText']]
			}, {
				name: 'transfer',
				headerText: this._('Transfer the information'),
				helpText: this._(''),
				widgets: [{
					type: 'Text',
					name: 'firstText',
					content: this._('The collected information can be transfered to Univention by uploading the data or by sending the data via mail. Please selected the corresponding button for the technique of your choice.') + '<br /><br />'
				}, {
					type: 'ComboBox',
					name: 'method',
					value: 'upload',
					label: this._('Method'),
					staticValues: [
						{id: 'upload', label: this._('Upload')},
						{id: 'mail', label: this._('Send mail')}
					]
				}],
				layout: [['firstText'],
						 ['method']]
			}, {
				name: 'mail',
				headerText: this._('Transfer via mail'),
				helpText: this._(''),
				widgets: [{
					type: 'Text',
					name: 'firstText',
					content: this._('To transfer the information via mail please follow these steps:<ol><li>Download the archive with the collected information and save it on your local system (find the link below)</li><li>Click on link Send mail to open your mail program</li><li>Attach the downloaded archive to the mail and send it to Univention</li><li>End this assistant by clicking on the button Finish</li></ol>') + '<br /><br />'
				}],
				layout: [['firstText']]
			}, {
				name: 'uploaded',
				headerText: this._('Transfered successfully'),
				helpText: this._(''),
				widgets: [{
					type: 'Text',
					name: 'firstText',
					content: this._('The information were transfered to Univention successfully.<br />Thank you very much for your support!') + '<br /><br />'
				}],
				layout: [['firstText']]
			}],

			canCancel: function() {
				return false;
			},

			next: function(currentID) {
				if (!currentID) {
					return 'general';
				}
				if (currentID == 'general') {
					if (this.getWidget('general', 'supportBox').get('value') === false) {
						return 'collect';
					} else {
						return 'support';
					}
				}
				if (currentID == 'support') {
					return 'collect';
				}
				if (currentID ==  'collect') {
					return 'transfer';
				}
				if (currentID == 'transfer') {
					if (this.getWidget('transfer', 'method') == 'upload') {
						return 'uploaded';
					} else {
						return 'mail';
					}
				}
			},

			previous: function(currentID) {
				if (currentID == 'support') {
					return 'general';
				}
				if (currentID == 'collect') {
					if (this.getWidget('general', 'supportBox').get('value') === false) {
						return 'general';
					} else {
						return 'support';
					}
				}
				if (currentID == 'transfer') {
					return 'collect';
				}
				if (currentID == 'mail') {
					return 'transfer';
				}
				if (currentID == 'uploaded') {
					return 'transfer';
				}
			},

			hasNext: function(currentID) {
				if (!this.pages.length) {
					return false;
				}
				if (currentID == 'mail') {
					return false;
				}
				return this.pages[this.pages.length - 1].name != currentID;
			},

			onFinished: dojo.hitch(this, function() {
					dojo.publish('/umc/tabs/close', [ this ]);
			})
		});

		this.addChild(this._wizard);
	}
});
