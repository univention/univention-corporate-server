/*
 * Copyright 2013-2014 Univention GmbH
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
	"umc/tools",
	"umc/dialog",
	"umc/widgets/TitlePane",
	"umc/widgets/Text",
	"umc/widgets/TextBox",
	"umc/widgets/TextArea",
	"umc/i18n!umc/modules/sysinfo"
], function(tools, dialog, TitlePane, Text, TextBox, TextArea, _) {
	return {
		traceback: function(traceback, feedbackLink) {
			dialog.confirmForm({
				title: _('Send to vendor'),
				widgets: [{
					type: Text,
					name: 'help',
					content: _('Information about the error will be sent to the vendor along with some data about the operating system.')
				}, {
					type: TitlePane,
					name: 'traceback',
					title: _('Show error message'),
					'class': 'umcTracebackPane',
					style: 'display: block;',
					open: false,
					content: '<pre>' + traceback + '</pre>'
				}, {
					type: TextArea,
					name: 'remark',
					label: _('Remarks (e.g. steps to reproduce) (optional)')
				}, {
					type: TextBox,
					name: 'email',
					label: _('Your email address (optional)')
				}]
			}).then(function(values) {
				values.traceback = traceback;
				tools.umcpCommand('sysinfo/traceback', values, false).then(
					function() {
						dialog.alert(_('Thank you for your help'));
					},
					function() {
						var alertString = _('Sending the information to the vendor failed');
						if (feedbackLink) {
							alertString += '. ' + _('You can also send the information via mail:') + ' ' + feedbackLink;
						}
						dialog.alert(alertString);
					}
				);
			});
		}
	};
});
