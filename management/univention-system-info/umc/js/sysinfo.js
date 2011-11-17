/*
 * Copyright 2011 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.sysinfo");

dojo.require("umc.i18n");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Wizard");

dojo.declare("umc.modules.sysinfo", [ umc.widgets.Module, umc.i18n.Mixin ], {

	// internal reference to the wizard
	_wizard: null,

	buildRendering: function() {
		this.inherited(arguments);

		this._wizard = new umc.modules._sysinfo.Wizard({});
		this.addChild(this._wizard);

		this.connect(this._wizard, 'onFinished', function() {
			dojo.publish('/umc/tabs/close', [ this ]);
		});
		this.connect(this._wizard, 'onCancel', function() {
			dojo.publish('/umc/tabs/close', [ this ]);
		});
	}
});


dojo.declare("umc.modules._sysinfo.Wizard", [ umc.widgets.Wizard, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {

	// use i18n information from umc.modules.sysinfo
	i18nClass: 'umc.modules.sysinfo',

	standbyOpacity: 1.00,

	_archiveFilename: null,
	_archiveLink: null,
	_mailLink: null,

	constructor: function() {
		this.pages = [{
			name: 'general',
			headerText: this._('General Information'),
			helpText: this._('<p>This module collects information about the hardware of your system. This might be helpful in connection with a support case. By transmitting the data to Univention you provide the information on which platforms UCS is currently used and therefore should be supported by newer versions. All information gathered by this module will be made anonymous before the transfer to Univention. In the following procedure you will be informed in detail about the each step.</p><p>No information is transmitted without your acceptance!</p>'),
			widgets: [{
				type: 'TextBox',
				name: 'manufacturer',
				label: this._('Manufacturer')
			}, {
				type: 'TextBox',
				name: 'model',
				label: this._('Model')
			}, {
				type: 'TextArea',
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
			layout: [['manufacturer', 'model'],
					 ['comment'],
					 ['supportBox'],
					 ['secondText']]
		}, {
			name: 'support',
			headerText: this._('Support Information'),
			helpText: this._(''),
			widgets: [{
				type: 'Text',
				name: 'firstText',
				content: this._('<p>If a Univention Support Engineer has asked you to provide these information, than please insert the ticket number of the related support ticket into the following text field. The ticket number can be found in the subject of a support mail of the ticket. This information will speed up the processing of the ticket.</p>')
			}, {
				type: 'TextBox',
				name: 'ticket',
				label: this._('This is related to a support case'),
				value: ''
			}, {
				type: 'Text',
				name: 'secondText',
				content: this._('<p>In the next step the information about the hardware of your system will be collect and a summary will be shown. No information will be send to Univention.</p>')
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
				content: this._('<p>The following information has been collected and will be transfered to Univention with your acceptance.</p>')
			}, {
				type: 'TextBox',
				name: 'cpu',
				label: this._('CPU'),
				value: ''
			}, {
				type: 'TextBox',
				name: 'num_cpu',
				label: this._('Number of CPUs'),
				value: ''
			}, {
				type: 'TextBox',
				name: 'mem',
				label: this._('Memory'),
				value: ''
			}, {
				type: 'TextBox',
				name: 'net_dev',
				label: this._('Network Device'),
				value: ''
			}, {
				type: 'TextBox',
				name: 'gfx_dev',
				label: this._('Graphics Device')
			}, {
				type: 'Text',
				name: 'secondText',
				content: this._('<p>Additionally to the information listed above some more details about your system has been collected. The hole set of collected data that will be transmitted to Univention can be downloaded at the following URL:</p>')
			}, {
				type: 'Text',
				name: 'download',
				content: this._('Archive with system information')
			}, {
				type: 'Text',
				name: 'thirdText',
				content: this._('In the following step two possibilities to transmit the information to Univention will be described.')
			}],
			layout: [['firstText'],
					 ['cpu'],
					 ['num_cpu'],
					 ['mem'],
					 ['net_dev'],
					 ['gfx_dev'],
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
				content: this._('<p>The collected information can be transfered to Univention by uploading the data or by sending the data via mail. Please selected the corresponding button for the technique of your choice.</p>')
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
			name: 'uploaded',
			headerText: this._('Transfered successfully'),
			helpText: this._(''),
			widgets: [{
				type: 'Text',
				name: 'firstText',
				content: this._('<p>The information were transfered to Univention successfully.</p><p>Thank you very much for your support!</p>')
			}],
			layout: [['firstText']]
		}, {
			name: 'mail',
			headerText: this._('Transfer via mail'),
			helpText: this._(''),
			widgets: [{
				type: 'Text',
				name: 'firstText',
				content: this._('To transfer the information via mail please follow these steps:<ol><li>Download the archive with the collected information and save it on your local system (find the link below)</li><li>Click on link Send mail to open your mail program</li><li>Attach the downloaded archive to the mail and send it to Univention</li><li>End this assistant by clicking on the button Finish</li></ol>')
			}, {
				type: 'Text',
				name: 'download',
				content: this._('Archive with system information')
			}, {
				type: 'Text',
				name: 'mail',
				content: 'Send Mail'
			}],
			layout: [['firstText'],
					 ['download'],
					 ['mail']]
		}];
	},

	buildRendering: function() {
		this.inherited(arguments);
		this._disableWidgets();
	},

	_disableWidgets: function() {
		var widgets = ['cpu', 'num_cpu', 'mem', 'net_dev', 'gfx_dev'];
		dojo.forEach(widgets, dojo.hitch(this, function(iwidget) {
			this.getWidget('collect', iwidget).set('disabled', true);
		}));
	},

	canCancel: function(pageName) {
		if (pageName == 'uploaded') {
			return false;
		} else {
			return true;
		}
	},

	hasNext: function(pageName) {
		if (pageName == 'uploaded') {
			return false;
		} else {
			return this.inherited(arguments);
		}
	},

	next: function() {
		var nextPage = this.inherited(arguments);
		if (nextPage == 'general') {
			this.standby(true);
			this.getGeneralInfo().then(
				dojo.hitch(this, function() {
					this.standby(false);
				})
			);
		}
		if (nextPage == 'support') {
			if (this.getWidget('general', 'supportBox').get('value') === false) {
				nextPage = 'collect';
			}
		}
		if (nextPage == 'collect') {
			this.standby(true);
			this.getSystemInfo().then(
				dojo.hitch(this, function() {
					this.standby(false);
				})
			);
		}
		if (nextPage == 'uploaded') {
			if (this.getWidget('transfer', 'method') == 'mail') {
				nextPage = 'mail';
			} else {
				this.standby(true);
				this.uploadArchive().then(
					dojo.hitch(this, function() {
						this.standby(false);
					})
				);
			}
		}
		if (nextPage == 'mail') {
			this.standby(true);
			this.getMailInfo().then(
				dojo.hitch(this, function() {
					this.standby(false);
				})
			);
		}
		return nextPage;
	},

	hasPrevious: function(pageName) {
		if (pageName == 'uploaded') {
			return false;
		} else {
			return this.inherited(arguments);
		}
	},

	previous: function() {
		var previousPage = this.inherited(arguments);
		if (previousPage == 'support') {
			if (this.getWidget('general', 'supportBox').get('value') === false) {
				return 'general';
			}
		}
		if (previousPage == 'uploaded') {
			if (this.getWidget('transfer', 'method') == 'mail') {
				return 'transfer';
			}
		}
		return previousPage;
	},

	getGeneralInfo: function() {
		var deferred = umc.tools.umcpCommand('sysinfo/general').then(
			dojo.hitch(this, function(data) {
				var generalPage = this.getPage('general');
				generalPage._form.setFormValues(data.result);
			})
		);
		return deferred;
	},

	getSystemInfo: function() {
		var generalValues =  this.getPage('general')._form.gatherFormValues();
		var supportValues =  this.getPage('support')._form.gatherFormValues();
		var requestValues = {
			'manufacturer': generalValues.manufacturer,
			'model': generalValues.model,
			'comment': generalValues.comment,
			'ticket': supportValues.ticket
		};
		var deferred = umc.tools.umcpCommand('sysinfo/system', requestValues).then(
			dojo.hitch(this, function(data) {
				this._archiveFilename = data.result.archive;
				this._archiveLink = dojo.replace('<a href="{url}">{text}</a>', {
					'url': '/univention-management-console/system-info/' + this._archiveFilename,
					'text': this._('Archive with system information')
				});

				var collectPage = this.getPage('collect');
				collectPage._form.setFormValues(data.result);
				this.getWidget('collect', 'download').set('content', this._archiveLink);

				this.getWidget('mail', 'download').set('content', this._archiveLink);
			})
		);
		return deferred;
	},

	getMailInfo: function() {
		var deferred = umc.tools.umcpCommand('sysinfo/mail').then(
			dojo.hitch(this, function(data) {
				this._mailLink = dojo.replace('<a href="{url}">{text}</a>', {
					'url': data.result.url,
					'text': this._('Send mail')
				});

				this.getWidget('mail', 'mail').set('content', this._mailLink);
			})
		);
		return deferred;
	},

	uploadArchive: function() {
		var values = {'archive': this._archiveFilename};
		var deferred = umc.tools.umcpCommand('sysinfo/upload', values);
		return deferred;
	}
});
