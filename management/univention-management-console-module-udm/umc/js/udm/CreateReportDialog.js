/*
 * Copyright 2011-2017 Univention GmbH
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
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dijit/Dialog",
	"umc/widgets/StandbyMixin",
	"umc/widgets/Form",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text",
	"umc/widgets/Button",
	"umc/widgets/ComboBox",
	"umc/i18n!umc/modules/udm"
], function(declare, lang, array, Dialog, StandbyMixin, Form, ContainerWidget, Text, Button, ComboBox, _) {
	return declare("umc.modules.udm.CreateReportDialog", [ Dialog, StandbyMixin ], {
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

			var _titleText = lang.hitch(this, function() {
				var text = {
					'users/user'        : _('Report for user'),
					'groups/group'      : _('Report for group'),
					'computers/computer': _('Report for computer'),
					'networks/network'  : _('Report for network object'),
					'dns/dns'           : _('Report for DNS object'),
					'dhcp/dhcp'         : _('Report for DHCP object'),
					'shares/share'      : _('Report for share'),
					'shares/print'      : _('Report for printer'),
					'mail/mail'         : _('Report for mail object'),
					'nagios/nagios'     : _('Report for Nagio object'),
					'policies/policy'   : _('Report for policy')
				}[this.moduleFlavor];
				if (!text) {
					text = _('Report for LDAP object');
				}
				return text;
			});

			// mixin the dialog title
			lang.mixin(this, {
				title: _titleText()
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			var _widgetsLabelText = lang.hitch(this, function(n) {
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
			});

			var reports = array.map(this.reports, function(item) {
				return {id: item, label: item};
			});

			var widgets = [{
				type: ComboBox,
				name: 'report',
				label: _widgetsLabelText(this.objects.length),
				description: _('The report template that should be used for the report.'),
				value: this.reports[0],
				staticValues: reports
			}];
			var layout = ['report'];

			// buttons
			var buttons = [ {
				name: 'create',
				label: _('Create'),
				defaultButton: true,
				callback: lang.hitch(this, function() {
					this.onDone(this._form.get('value'));
				})
			}, {
				name: 'cancel',
				label: _('Cancel'),
				callback: lang.hitch(this, function() {
					this.destroyRecursive();
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

		onDone: function(options) {
			var _waitingContentText = lang.hitch(this, function(n) {
				var text = {
					'users/user'        : _.ngettext('<p>Generating user report for one object.</p>',
					                                  '<p>Generating user report for %d objects.</p>', n),
					'groups/group'      : _.ngettext('<p>Generating group report for one object.</p>',
					                                  '<p>Generating group report for %d objects.</p>', n),
					'computers/computer': _.ngettext('<p>Generating computer report for one object.</p>',
					                                  '<p>Generating computer report for %d objects.</p>', n),
					'networks/network'  : _.ngettext('<p>Generating network object report for one object.</p>',
					                                  '<p>Generating network object report for %d objects.</p>', n),
					'dns/dns'           : _.ngettext('<p>Generating DNS object report for one object.</p>',
					                                  '<p>Generating DNS object report for %d objects.</p>', n),
					'dhcp/dhcp'         : _.ngettext('<p>Generating DHCP object report for one object.</p>',
					                                  '<p>Generating DHCP object report for %d objects.</p>', n),
					'shares/share'      : _.ngettext('<p>Generating share report for one object.</p>',
					                                  '<p>Generating share report for %d objects.</p>', n),
					'shares/print'      : _.ngettext('<p>Generating printer report for one object.</p>',
					                                  '<p>Generating printer report for %d objects.</p>', n),
					'mail/mail'         : _.ngettext('<p>Generating mail object report for one object.</p>',
					                                  '<p>Generating mail object report for %d objects.</p>', n),
					'nagios/nagios'     : _.ngettext('<p>Generating Nagios object report for one object.</p>',
					                                  '<p>Generating Nagios object report for %d objects.</p>', n),
					'policies/policy'   : _.ngettext('<p>Generating policy report for one object.</p>',
					                                  '<p>Generating policy report for %d objects.</p>', n)
				}[this.moduleFlavor];
				if (!text) {
					text = _.ngettext('<p>Generating LDAP object report for one object.</p>',
					                   '<p>Generating LDAP object report for %d objects.</p>', n);
				}
				text += '<p>This may take a while</p>';
				return text;
			});
			var _standbyDuringSuccessText = lang.hitch(this, function(type, href) {
				var obj = {
					'users/user'        : _('user report'),
					'groups/group'      : _('group report'),
					'computers/computer': _('computer report'),
					'networks/network'  : _('network object report'),
					'dns/dns'           : _('DNS object report'),
					'dhcp/dhcp'         : _('DHCP object report'),
					'shares/share'      : _('share report'),
					'shares/print'      : _('printer report'),
					'mail/mail'         : _('mail object report'),
					'nagios/nagios'     : _('Nagios object report'),
					'policies/policy'   : _('policy report')
				}[this.moduleFlavor];
				if (!obj) {
					obj = _('LDAP object report');
				}
				return lang.replace(_('The {type} can be downloaded at<br><br><a target="_blank" href="{href}">{obj}</a>'), {type: type, href: href, obj: obj});
			});

			var waiting = new Text({
				content: _waitingContentText(this.objects.length)
			});
			this._container.addChild(waiting, 0);

			this.set('title', _('Creating the report ...'));

			this.standbyDuring(this.umcpCommand('udm/reports/create', {objects: this.objects, report: options.report}, this._form)).then(lang.hitch(this, function(data) {
				this._container.removeChild(this._form);
				this._container.removeChild(waiting);
				waiting.destroy();

				var message = lang.replace('<p>{0}</p>', [_standbyDuringSuccessText(options.report, data.result.URL)]);
				this.set('title', _('Report has been created'));
				this._container.addChild(new Text({content: message}));

				var btnContainer = new ContainerWidget({
					style: 'text-align: center;',
					'class' : 'umcButtonRow'
				});
				btnContainer.addChild(new Button({
					defaultButton: true,
					label: _('Close'),
					style: 'margin-left: auto;',
					callback: lang.hitch(this, function() {
						this.destroyRecursive();
					})
				}));
				this._container.addChild(btnContainer);
			}), lang.hitch(this, function() {
				this._container.removeChild(waiting);
			}));
		}
	});
});
