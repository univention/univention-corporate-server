/*
 * Copyright 2013 Univention GmbH
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
/*global define require console window $*/

define([
	"./startsite",
	"dojo/io-query",
	"dojo/_base/lang",
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/query",
	"dojo/dom-construct",
	"dojo/dom-attr",
	"dojo/dom-style",
	"dojo/dom-class",
	"dojo/on",
	"dojo/json",
	"dojo/text!entries.json",
	"dojo/text!languages.json",
	"/ucs-overview/js/i18n!js/appliance,js"
], function(startsite, ioQuery, lang, kernel, array, query, domConstruct, domAttr, domStyle, domClass, on, json, entriesStr, languagesStr, _) {
	var module = lang.mixin({}, startsite, {
		_updateNoScriptElements: function() {
			var dropdown = query('#header-right .dropdown')[0];
			var navtabs = query('#site-header .nav-tabs')[0];
			domStyle.set(dropdown, 'display', 'inherit');
			// domStyle.set(navtabs, 'display', 'inherit');
		},

		start: function() {
			this._updateNoScriptElements();
			// this._updateLinkEntries();
			this._updateLocales();
			this._updateTranslations();
			// this._registerHashChangeEvent();
			// this._updateActiveTab();
		}
	});

	// add data-i18n attribute for HTML code
	module._translations = lang.mixin({}, module._translations, {
		setupTitle: _('Welcome to UCS initial configuration'),
		setupText: _('This machine is currently being configured by cloud-init.'),
		setupText2: _('The configuration you selected is applied and the Univention Corporate Server installation is finished.'),
		setupSshCommand: _('ssh -i &lt;path/to/privatekey&gt; root@&lt;serveraddress&gt; passwd'),
		setupText3: _('After the setup has finished, you will be redirected. Alternatively, after setup is finished, you can  '),
		setupLinkText: _('use this link to reach the overview page')
	});

	return module;
});

