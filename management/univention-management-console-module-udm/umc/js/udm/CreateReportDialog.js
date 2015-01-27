/*
 * Copyright 2011-2015 Univention GmbH
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

		// LDAP object type name in singular and plural
		objectNameSingular: '',
		objectNamePlural: '',

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
				title: _('Report for %s', this.objectNameSingular)
			});
		},

		buildRendering: function() {
			this.inherited(arguments);

			var reports = array.map(this.reports, function(item) {
				return {id: item, label: item};
			});

			var widgets = [{
				type: ComboBox,
				name: 'report',
				label: _('Report for %d %s', this.objects.length, this.objects.length === 1 ? this.objectNameSingular : this.objectNamePlural),
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

			var waiting = new Text({
				content: _('<p>Generating %s report for %d objects.</p><p>This may take a while</p>', this.objectNameSingular, this.objects.length)
			});
			this._container.addChild(waiting, 0);

			this.set('title', _('Creating the report ...'));

			var request_data = {objects: this.objects, report: options.report};
			this.standbyDuring(this.umcpCommand('udm/reports/create', request_data, this._form)).then(lang.hitch(this, function(data) {
				var title = '';
				var message = '';

				this._container.removeChild(this._form);
				this._container.removeChild(waiting);
				waiting.destroy();

				if (true === data.result.success) {
					message = lang.replace('<p>{0}</p>', [_('The %s can be downloaded at<br><br><a target="_blank" href="%s">%s report</a>', data.result.docType, data.result.URL, this.objectNameSingular)]);
					title = _('Report has been created');
				} else {
					title = _('Report creation has failed');
					message = _('The report could not be created. Details for the problems can be found in the log files.');
				}
				this.set('title', title);
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
