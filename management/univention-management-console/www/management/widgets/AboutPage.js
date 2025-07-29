/*
 * SPDX-FileCopyrightText: 2014-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
