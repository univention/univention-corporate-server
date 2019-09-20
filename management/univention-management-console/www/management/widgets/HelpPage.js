/*
 * Copyright 2014-2019 Univention GmbH
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
	"umc/widgets/Text",
	"umc/i18n!management"
], function(Text, _) {
	return {
		name: 'help',
		headerText: _('Further Information'),
		'class': 'umcAppDialogPage umcAppDialogPage-help',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text',
			content: _('<p>Detailed usage information on Univention Management Console can be found in the UCS manual. The manual as well as further important information are available via the following links:</p>')
		}, {
			type: Text,
			name: 'links',
			content: _('<ul><li><a href="https://docs.software-univention.de/" target="_blank">Online documentation</a></li><li><a href="https://wiki.univention.de/index.php?title=Hauptseite" target="_blank">Univention Wiki</a></li><li><a href="https://www.univention.com/products/support/community-support/" target="_blank">Community and support</a></li></ul>')
		}]
	};
});
