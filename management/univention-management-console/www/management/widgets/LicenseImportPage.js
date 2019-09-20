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
	"dojo/Deferred",
	"umc/tools",
	"umc/widgets/Text",
	"umc/widgets/Uploader",
	"umc/i18n!management"
], function(lang, Deferred, tools, Text, Uploader, _) {
	var pageConf = {
		name: 'licenseImport',
		headerText: _('License import'),
		'class': 'umcAppDialogPage umcAppDialogPage-licenseImport',
		navBootstrapClasses: 'col-xxs-12 col-xs-4',
		mainBootstrapClasses: 'col-xxs-12 col-xs-8',
		widgets: [{
			type: Text,
			name: 'text1',
			content: _('<p><b>You have got mail!</b></p><p>A license file should have been sent to your email address. Upload the license file from the email to activate your UCS instance.</p>')
		}, {
			type : Uploader,
			name : 'licenseUpload',
			buttonLabel: _('Upload license file...'),
			command: 'udm/license/import',
			_progressDeferred: null,
			onUploadStarted: function() {
				this._progressDeferred = new Deferred();
				this._progressDeferred.progress(_('Importing license data...'));
				this.onImportLicense(this._progressDeferred);
			},
			onUploaded: function(result) {
				if (result.success) {
					this._progressDeferred.progress(_('Updating session data...'));
					tools.renewSession().then(lang.hitch(this, function() {
						this._progressDeferred.resolve();
						//dialog.alert(_('The license has been imported successfully.'));
					}));
				}
				else {
					this._progressDeferred.reject(result.message);
				}
			},
			onImportLicense: function(deferred) {
				// event stub
			}
		}, {
			type: Text,
			name: 'text2',
			content: '<p>' + _('You may as well import the license file at a later point in time via the user menu in the top right.') + '</p>'
		}],

		// the following values will be loaded via UCR
		hasLicense: null,
		hasLicenseRequested: null,
		showInStartupDialog: function(wizardValues) {
			return !this.hasLicense && (this.hasLicenseRequested || lang.trim(wizardValues.email));
		}
	};

	var _ucrDeferred = null;
	var ucr = function() {
		if (!_ucrDeferred) {
			_ucrDeferred = tools.ucr(['uuid/license', 'ucs/web/license/requested']).then(function(ucr) {
				return {
					hasLicense: Boolean(ucr['uuid/license']),
					hasLicenseRequested: tools.isTrue(ucr['ucs/web/license/requested'])
				};
			});
		}
		return _ucrDeferred;
	};

	// return an AMD plugin that resolves when the UCR variables have been loaded
	return {
		load: function (params, req, load, config) {
			ucr().then(function(info) {
				load(lang.mixin(pageConf, info));
			});
		}
	};
});
