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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/date/locale",
	"umc/tools",
	"umc/widgets/Text",
	"umc/i18n!management"
], function(lang, array, locale, tools, Text, _) {
	var pageConf = {
		name: 'about',
		'class': 'umcAppDialogPage umcAppDialogPage-about',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		headerText: _('Univention Management Console'),
		widgets: [{
			content: '{server}',
			label: '<b>' + _('Server') + '</b>'
		}, {
			content: '{ucs_version}',
			label: '<b>' + _('UCS Version') + '</b>'
		}, {
			content: '{umc_version}',
			label: '<b>' + _('UMC Version') + '</b>'
		}, {
			content: '{ssl_validity_root}',
			label: '<b>' + _('Date of expiry of the SSL root certificate') + '</b>'
		}, {
			content: '{ssl_validity_host}',
			label: '<b>' + _('Date of expiry of the SSL certificate for this system') + '</b>'
		}]
	};

	var _formatDate = function(timestamp) {
		return locale.format(new Date(timestamp), {
			fullYear: true,
			timePattern: " ",
			formatLength: "long"
		});
	};

	var _pageConfDeferred = null;
	var loadPageConf = function() {
		if (!_pageConfDeferred) {
			_pageConfDeferred = tools.umcpCommand('get/info').then(function(response) {
				// format dates
				var data = response.result;
				array.forEach(['ssl_validity_host', 'ssl_validity_root'], function(ikey) {
					data[ikey] = _formatDate(data[ikey]);
				});

				// replace variables in content strings of the widget definitions
				// and set common properties
				array.forEach(pageConf.widgets, function(iwidget, idx) {
					iwidget.type = Text;
					iwidget.name = 'text' + idx;
					iwidget.labelPosition = 'top';
					iwidget.content = lang.replace(iwidget.content, data);
				});
				return pageConf;
			});
		}
		return _pageConfDeferred;
	};

	return {
		load: function (params, req, load, config) {
			loadPageConf().then(function(pageConf) {
				load(pageConf);
			});
		}
	};
});
