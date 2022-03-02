/*
 * Copyright 2021-2022 Univention GmbH
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
	"umc/tools",
	"umc/widgets/Module",
	"umc/widgets/Page",
	"management/widgets/ActivationDialog",
	"umc/modules/udm/LicenseDialog",
	"umc/modules/udm/LicenseImportDialog",
	"./welcome/Bubble",
	"./welcome/BubbleButton",
	"umc/i18n!umc/modules/welcome",
	"xstyle/css!umc/modules/welcome.css"
], function(declare, tools, Module, Page, ActivationDialog, LicenseDialog, LicenseImportDialog, Bubble, BubbleButton, _) {
	return declare("umc.modules.welcome", [ Module ], {

		buildRendering: function() {
			this.inherited(arguments);

			tools.ucr(['uuid/license']).then((ucr) => {
				this._page = new Page({
					helpText: _('Great to see you! This page lets you upload a UCS license so you can start using the Univention App Center.'),
					fullWidth: true
				});
				this.addChild(this._page);

				var license = new Bubble({
					header: _('UCS License'),
					icon: 'modules/udm/license.svg',
					description: _('Manage your license for your Univention Corporate Server domain'),
				});
				if (!ucr['uuid/license']) {
					license.addChild(new BubbleButton({
						header: _('Request a new license'),
						description: _('We send you a license with a Key ID to your email address'),
						onClick: () => { new ActivationDialog({}); }
					}));
				}
				license.addChild(new BubbleButton({
					header: _('License info'),
					description: _('Show your current license'),
					onClick: () => { new LicenseDialog({}); }
				}));
				license.addChild(new BubbleButton({
					header: _('Import a license'),
					description: _('Upload a new license we sent you earlier'),
					onClick: () => {
						var dlg = new LicenseImportDialog({});
						dlg.show();
					}
				}));
				this._page.addChild(license);
			});
		}
	});
});
