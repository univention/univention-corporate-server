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
/*global define require*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/topic",
	"umc/widgets/Module",
	"umc/modules/appcenter/AppDetailsPage",
	"umc/modules/appcenter/AppChooseHostDialog",
	"umc/modules/appcenter/AppDetailsDialog",
	"umc/i18n!umc/modules/apps"
], function(declare, lang, topic, Module, AppDetailsPage, AppChooseHostDialog, AppDetailsDialog, _) {
	return declare("umc.modules.apps", Module, {
		buildRendering: function() {
			this.inherited(arguments);
			var udmAccessible = false;
			try {
				require('umc/modules/udm');
				udmAccessible = true;
			} catch(e) {
			}
			this._dialog =  new AppDetailsDialog({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this._choose = new AppChooseHostDialog({
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this._page = new AppDetailsPage({
				app: {id: this.moduleFlavor},
				moduleID: this.moduleID,
				moduleFlavor: this.moduleFlavor,
				backLabel: _('Close'),
				getAppCommand: 'apps/get',
				detailsDialog: this._dialog,
				hostDialog: this._choose,
				udmAccessible: udmAccessible,
				standby: lang.hitch(this, 'standby'),
				standbyDuring: lang.hitch(this, 'standbyDuring')
			});
			this._page.on('back', lang.hitch(this, function() {
				topic.publish('/umc/tabs/close', this);
			}));
			this.standbyDuring(this._page.appLoadingDeferred);
			this.addChild(this._dialog);
			this.addChild(this._choose);
			this.addChild(this._page);
			this.selectChild(this._page);
			this._dialog.on('showUp', lang.hitch(this, function() {
				this.selectChild(this._dialog);
			}));
			this._choose.on('showUp', lang.hitch(this, function() {
				this.selectChild(this._choose);
			}));
			this._choose.on('back', lang.hitch(this, function() {
				this.selectChild(this._page);
			}));
			this._dialog.on('back', lang.hitch(this, function() {
				this.selectChild(this._page);
			}));
		}

	});
});

