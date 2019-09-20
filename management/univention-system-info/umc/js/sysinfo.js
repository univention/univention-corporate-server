/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/topic",
	"umc/tools",
	"umc/widgets/Module",
	"umc/widgets/Wizard",
	"umc/widgets/StandbyMixin",
	"umc/widgets/ComboBox",
	"umc/widgets/TextBox",
	"umc/widgets/Text",
	"umc/widgets/TextArea",
	"umc/widgets/CheckBox",
	"umc/i18n!umc/modules/sysinfo",
	"umc/modules/sysinfo/lib" // FIXME: needs to live here to be loaded
], function(declare, lang, array, topic, tools, Module, Wizard, StandbyMixin, ComboBox, TextBox, Text, TextArea, CheckBox, _) {

	var SysinfoWizard = declare("umc.modules.sysinfo.Wizard", [ Wizard, StandbyMixin ], {

		standbyOpacity: 1.00,

		_archiveFilename: null,
		_archiveLink: null,
		_mailLink: null,

		constructor: function() {
			this.pages = [{
				name: 'general',
				headerText: _('General information'),
				helpText: _('<p>This module collects information about the hardware of your system. This might be helpful in connection with a support case. By transmitting the data to Univention you provide the information on which platforms UCS is currently used and therefore should be supported by newer versions. In the following procedure you will be informed in detail about the each step.</p><p>No information is transmitted without your acceptance</p>'),
				widgets: [{
					type: TextBox,
					name: 'manufacturer',
					label: _('Manufacturer')
				}, {
					type: TextBox,
					name: 'model',
					label: _('Model')
				}, {
					type: TextArea,
					name: 'comment',
					label: _('Comment')
				}, {
					type: CheckBox,
					name: 'supportBox',
					label: _('This is related to a support case')
				}, {
					type: Text,
					name: 'secondText',
					label: _('If this is related to a support case the next step will be to enter the ticket number. Otherwise the information about your system will be collected and a summary is shown.')
				}],
				layout: [['manufacturer', 'model'],
					 	 ['comment'],
					 	 ['supportBox'],
					 	 ['secondText']]
			}, {
				name: 'support',
				headerText: _('Support information'),
				helpText: '',
				widgets: [{
					type: Text,
					name: 'firstText',
					content: _('<p>If a Univention Support Engineer has asked you to provide this information, then please insert the ticket number of the related support ticket into the following text field. The ticket number can be found in the subject of a support mail of the ticket. This information will speed up the processing of the ticket.</p>')
				}, {
					type: TextBox,
					name: 'ticket',
					label: _('Ticket'),
					value: ''
				}, {
					type: Text,
					name: 'secondText',
					content: _('<p>In the next step the information about the hardware of your system will be collected and a summary will be shown. During this step, no information will be sent to Univention.</p>')
				}],
				layout: [['firstText'],
					 	 ['ticket'],
					 	 ['secondText']]
			}, {
				name: 'collect',
				headerText: _('Collected data'),
				helpText: '',
				widgets: [{
					type: Text,
					name: 'firstText',
					content: _('<p>The following information has been collected and will be transferred to Univention with your acceptance.</p>')
				}, {
					type: TextBox,
					name: 'cpu',
					label: _('CPU'),
					value: ''
				}, {
					type: TextBox,
					name: 'num_cpu',
					sizeClass: 'OneThird',
					label: _('Number of CPUs'),
					value: ''
				}, {
					type: TextBox,
					name: 'mem',
					label: _('Memory'),
					value: ''
				}, {
					type: TextBox,
					name: 'net_dev',
					label: _('Network adapter'),
					value: ''
				}, {
					type: TextBox,
					name: 'gfx_dev',
					label: _('Graphics card')
				}, {
					type: Text,
					name: 'secondText',
					content: _('<p>Additionally to the information listed above some more details about the system has been collected. The whole set of collected data that will be transmitted to Univention can be downloaded at the following URL:</p>')
				}, {
					type: Text,
					name: 'download',
					content: _('Archive with system information')
				}, {
					type: Text,
					name: 'thirdText',
					content: _('In the following step two possibilities to transmit the information to Univention will be described.')
				}],
				layout: [['firstText'],
					 	 ['cpu', 'num_cpu'],
					 	 ['mem'],
					 	 ['net_dev'],
					 	 ['gfx_dev'],
					 	 ['secondText'],
					 	 ['download'],
					 	 ['thirdText']]
			}, {
				name: 'transfer',
				headerText: _('Transfer the information'),
				helpText: _(''),
				widgets: [{
					type: Text,
					name: 'firstText',
					content: _('<p>The collected information can be transferred to Univention by uploading the data or by sending it via mail. Please select the corresponding option.</p>')
				}, {
					type: ComboBox,
					name: 'method',
					value: 'upload',
					label: _('Method'),
					staticValues: [
						{id: 'upload', label: _('Upload')},
						{id: 'mail', label: _('Send mail')}
					]
				}],
				layout: [['firstText'],
					 	 ['method']]
			}, {
				name: 'uploaded',
				headerText: _('Transferred successfully'),
				helpText: '',
				widgets: [{
					type: Text,
					name: 'firstText',
					content: _('<p>The information were transferred to Univention successfully.</p><p>Thank you very much for your support!</p>')
				}],
				layout: [['firstText']]
			}, {
				name: 'mail',
				headerText: _('Transfer via mail'),
				helpText: '',
				widgets: [{
					type: Text,
					name: 'firstText',
					content: _('To transfer the information via mail please follow these steps:<ol><li>Download the archive with the collected information and save it on your local system</li><li>Click on link <i>Send mail</i> to open your mail program</li><li>Attach the downloaded archive to the mail and send it to Univention</li><li>End this assistant by clicking on the button <i>Finish</i></li></ol>')
				}, {
					type: Text,
					name: 'download',
					content: _('Archive with system information')
				}, {
					type: Text,
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
			array.forEach(widgets, lang.hitch(this, function(iwidget) {
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
				this.getGeneralInfo();
			}
			if (nextPage == 'support') {
				if (this.getWidget('general', 'supportBox').get('value') === false) {
					nextPage = 'collect';
				}
			}
			if (nextPage == 'collect') {
				this.getSystemInfo();
			}
			if (nextPage == 'uploaded') {
				if (this.getWidget('transfer', 'method') == 'mail') {
					nextPage = 'mail';
				} else {
					return this.uploadArchive().then(function() {
						return nextPage;
					}, lang.hitch(this, function() {
						this.getPage('uploaded').set('headerText', _('Uploading failed'));
						this.getWidget('uploaded', 'firstText').set('content', _('<p>The information could not be transferred to Univention.</p><p>You can send them as email!</p>'));
						return nextPage;
					}));
				}
			}
			if (nextPage == 'mail') {
				this.getMailInfo();
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
			this.standbyDuring(tools.umcpCommand('sysinfo/general')).then(
				lang.hitch(this, function(data) {
					var generalPage = this.getPage('general');
					generalPage._form.setFormValues(data.result);
				})
			);
		},

		getSystemInfo: function() {
			var generalValues =  this.getPage('general')._form.get('value');
			var supportValues =  this.getPage('support')._form.get('value');
			var requestValues = {
				'manufacturer': generalValues.manufacturer,
				'model': generalValues.model,
				'comment': generalValues.comment,
				'ticket': supportValues.ticket
			};
			this.standbyDuring(tools.umcpCommand('sysinfo/system', requestValues)).then(
				lang.hitch(this, function(data) {
					this._archiveFilename = data.result.archive;
					this._archiveLink = lang.replace('<a href="{url}">{text}</a>', {
						'url': '/univention/system-info/' + this._archiveFilename,
						'text': _('Archive with system information')
					});

					var collectPage = this.getPage('collect');
					collectPage._form.setFormValues(data.result);
					this.getWidget('collect', 'download').set('content', this._archiveLink);

					this.getWidget('mail', 'download').set('content', this._archiveLink);
				})
			);
		},

		getMailInfo: function() {
			this.standbyDuring(tools.umcpCommand('sysinfo/mail')).then(
				lang.hitch(this, function(data) {
					this._mailLink = lang.replace('<a href="{url}">{text}</a>', {
						'url': data.result.url,
						'text': _('Send mail')
					});

					this.getWidget('mail', 'mail').set('content', this._mailLink);
				})
			);
		},

		uploadArchive: function() {
			var values = {'archive': this._archiveFilename};
			return this.standbyDuring(tools.umcpCommand('sysinfo/upload', values));
		}
	});

	return declare("umc.modules.sysinfo", [ Module ], {

		// internal reference to the wizard
		_wizard: null,

		buildRendering: function() {
			this.inherited(arguments);

			this._wizard = new SysinfoWizard({});
			this.addChild(this._wizard);

			this._wizard.on('Finished', lang.hitch(this, function() {
				topic.publish('/umc/tabs/close', this);
			}));
			this._wizard.on('Cancel', lang.hitch(this, function() {
				topic.publish('/umc/tabs/close', this);
			}));
		}
	});

});
