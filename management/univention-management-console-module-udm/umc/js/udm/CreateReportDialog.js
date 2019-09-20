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
	"dijit/Dialog",
	"umc/tools",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/ProgressBar",
	"umc/widgets/ComboBox",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, Dialog, tools, Form, ContainerWidget, ProgressBar, ComboBox, _) {
	return declare("umc.modules.udm.CreateReportDialog", [ Dialog ], {
		// summary:
		//		Dialog class for creating Univention Directory Reports.

		// umcpCommand: Function
		//		Reference to the module specific umcpCommand function.
		umcpCommand: null,

		// moduleFlavor: String
		//		Specifies the flavor of the module. This property is necessary to decide what
		//		kind of dialog is presented: in the context of a particular UDM module or
		//		the UDM navigation.
		moduleFlavor: '',

		// LDAP DNs to include in the report
		objects: null,

		// list of available reports
		reports: null,

		// internal reference to the dialog's form
		_form: null,

		_container: null,

		'class' : 'umcPopup',

		// force max-width
		style: 'max-width: 400px;',

		postMixInProperties: function() {
			this.inherited(arguments);

			// mixin the dialog title
			lang.mixin(this, {
				title: this._widgetsLabelText(this.objects.length)
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			var widgets = [{
				type: ComboBox,
				name: 'report',
				label: this._widgetsLabelText(this.objects.length),
				description: _('The report template that should be used for the report.'),
				staticValues: this.reports
			}];
			var layout = ['report'];

			// buttons
			var buttons = [ {
				name: 'cancel',
				label: _('Cancel'),
				callback: lang.hitch(this, function() {
					this.destroyRecursive();
				})
			}, {
				name: 'submit',
				label: _('Create'),
				callback: lang.hitch(this, function() {
					this.onDone(this._form.get('value'));
				})
			} ];

			// now create a Form
			this._form = new Form({
				widgets: widgets,
				layout: layout,
				buttons: buttons
			});
			this._container = new ContainerWidget({});
			this._container.addChild(this._form);
			this.set('content', this._container);
		},

		_widgetsLabelText: function(n) {
			var text = {
				'users/user'        : _.ngettext('Report for user', 'Report for %d users', n),
				'groups/group'      : _.ngettext('Report for group', 'Report for %d groups', n),
				'computers/computer': _.ngettext('Report for computer', 'Report for %d computers', n),
				'networks/network'  : _.ngettext('Report for network object', 'Report for %d network objects', n),
				'dns/dns'           : _.ngettext('Report for DNS object', 'Report for %d DNS objects', n),
				'dhcp/dhcp'         : _.ngettext('Report for DHCP object', 'Report for %d DHCP objects', n),
				'shares/share'      : _.ngettext('Report for share', 'Report for %d shares', n),
				'shares/print'      : _.ngettext('Report for printer', 'Report for %d printers', n),
				'mail/mail'         : _.ngettext('Report for mail object', 'Report for %d mail objects', n),
				'nagios/nagios'     : _.ngettext('Report for Nagios object', 'Report for %d Nagios objects', n),
				'policies/policy'   : _.ngettext('Report for policy', 'Report for %d policies', n)
			}[this.moduleFlavor];
			if (!text) {
				text = _.ngettext('Report for LDAP object', 'Report for %d LDAP objects', n);
			}
			return text;
		},

		onDone: function(options) {
			var _waitingContentText = lang.hitch(this, function(n) {
				var text = {
					'users/user'        : _.ngettext('Generating user report for one object.',
					                                 'Generating user report for %d objects.', n),
					'groups/group'      : _.ngettext('Generating group report for one object.',
					                                 'Generating group report for %d objects.', n),
					'computers/computer': _.ngettext('Generating computer report for one object.',
					                                 'Generating computer report for %d objects.', n),
					'networks/network'  : _.ngettext('Generating network object report for one object.',
					                                 'Generating network object report for %d objects.', n),
					'dns/dns'           : _.ngettext('Generating DNS object report for one object.',
					                                 'Generating DNS object report for %d objects.', n),
					'dhcp/dhcp'         : _.ngettext('Generating DHCP object report for one object.',
					                                 'Generating DHCP object report for %d objects.', n),
					'shares/share'      : _.ngettext('Generating share report for one object.',
					                                 'Generating share report for %d objects.', n),
					'shares/print'      : _.ngettext('Generating printer report for one object.',
					                                 'Generating printer report for %d objects.', n),
					'mail/mail'         : _.ngettext('Generating mail object report for one object.',
					                                 'Generating mail object report for %d objects.', n),
					'nagios/nagios'     : _.ngettext('Generating Nagios object report for one object.',
					                                 'Generating Nagios object report for %d objects.', n),
					'policies/policy'   : _.ngettext('Generating policy report for one object.',
					                                 'Generating policy report for %d objects.', n)
				}[this.moduleFlavor];
				if (!text) {
					text = _.ngettext('Generating LDAP object report for one object.',
					                   'Generating LDAP object report for %d objects.', n);
				}
				text += ' ' + _('This may take a while.');
				return text;
			});

			var progress = new ProgressBar();
			this.own(progress);
			progress.setInfo(_('Creating the report...'), _waitingContentText(this.objects.length), Infinity);

			this.hide();
			this.standbyDuring(this.umcpCommand('udm/reports/create', {objects: this.objects, report: options.report}, this._form), progress).then(lang.hitch(this, function(data) {
				var link = document.createElement('a');
				this._container.domNode.appendChild(link);
				link.href = data.result.URL;
				link.download = link.href.substr(link.href.lastIndexOf('=') + 1);
				link.click();
				this.destroyRecursive();
			}), lang.hitch(this, function(error) {
				if (tools.parseError(error).status === 422) {
					this.show();
					return;
				}
				this.destroyRecursive();
			}));
		}
	});
});
