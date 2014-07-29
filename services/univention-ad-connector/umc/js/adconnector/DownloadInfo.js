/*
 * Copyright 2014 Univention GmbH
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

/*global define */

define([
	"dojo/_base/declare",
	"umc/widgets/Text",
	"umc/i18n!umc/modules/adconnector"
], function(declare, Text, _) {
	return declare("umc.modules.adconnector.DownloadInfo", Text, {
		configured: false,

		_setConfiguredAttr: function(configured) {
			var downloadText = _('The MSI files are the installation files for the password service and can be started by double clicking on it.') + '<br>' +
			_('The package is installed in the <b>C:\\Windows\\UCS-AD-Connector</b> directory automatically. Additionally, the password service is integrated into the Windows environment as a system service, which means the service can be started automatically or manually.') +
			'<ul><li><a href="/univention-ad-connector/ucs-ad-connector.msi">ucs-ad-connector.msi</a><br>' +
			_('Installation file for the password service for <b>%s</b> Windows.<br />It can be started by double clicking on it.', '32bit') +
			'</li><li><a href="/univention-ad-connector/ucs-ad-connector-64bit.msi">ucs-ad-connector-64bit.msi</a><br>' +
			_('Installation file for the password service for <b>%s</b> Windows.<br />It can be started by double clicking on it.', '64bit') +
			'</li><li><a href="/univention-ad-connector/vcredist_x86.exe">vcredist_x86.exe</a><br>' +
			_('Microsoft Visual C++ 2010 Redistributable Package (x86) - <b>Must</b> be installed on a <b>64bit</b> Windows.') +
			'</li>';

			if (configured) {
				downloadText += '<li><a href="/umcp/command/adconnector/cert.pem" type="application/octet-stream">cert.pem</a><br>' +
				_('The <b>cert.pem</b> file contains the SSL certificates created in UCS for secure communication.') + ' ' +
				_('It must be copied into the installation directory of the password service.') +
				_('<br />Please verify that the file has been downloaded as <b>cert.pem</b>, Internet Explorer appends a .txt under some circumstances.') +
				'</li><li><a href="/umcp/command/adconnector/private.key" type="application/octet-stream">private.key</a><br>' +
				_('The <b>private.key</b> file contains the private key to the SSL certificates.') + ' ' +
				_('It must be copied into the installation directory of the password service.') +
				'</li>';
			}
			downloadText += '</ul>';
			this.set('content', downloadText);
		}
	});
});

