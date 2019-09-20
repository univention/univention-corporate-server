/*
 * Copyright 2015-2019 Univention GmbH
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
], function(declare) {
	return declare("umc.modules.appcenter._AppDialogMixin", null, {
		app: null,
		noFooter: true,
		'class': 'umcAppCenterDialog',
		_initialBootstrapClasses: 'col-xs-12 col-sm-12 col-md-10 col-md-offset-1 col-lg-8 col-lg-offset-2',
		headerTextAllowHTML: false,
		helpTextAllowHTML: false,
		headerTextRegion: 'main',
		helpTextRegion: 'main',

		_clearWidget: function(attr, remove) {
			if (!this[attr]) {
				// nothing to do
				return;
			}
			if (remove) {
				this.removeChild(this[attr]);
			}
			this[attr].destroyRecursive();
			this[attr] = null;
		},

		onUpdate: function() {
		},

		onShowUp: function() {
		},

		onNext: function() {
		},

		onBack: function() {
		}
	});
});

