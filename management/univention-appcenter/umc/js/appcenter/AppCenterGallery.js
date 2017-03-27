/*
 * Copyright 2013-2017 Univention GmbH
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
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/AppGallery",
	"umc/i18n!umc/modules/appcenter"
], function(declare, domClass, entities, tools, AppGallery, _) {
	return declare("umc.modules.appcenter.AppCenterGallery", [ AppGallery ], {
		iconClassPrefix: 'umcAppCenter',

		postMixInProperties: function() {
			this.inherited(arguments);
			this.baseClass += ' umcAppCenterGallery';
		},

		postCreate: function() {
			// TODO: this changes with Dojo 2.0
			this.domNode.setAttribute("widgetId", this.id);

			// add specific DOM classes
			if (this.baseClass) {
				domClass.add(this.domNode, this.baseClass);
			}

			if (this.actions) {
				this._setActions(this.actions);
			}
			if (this.store) {
				this.set('store', this.store);
			}
		},

		getStatusIconClass: function(item) {
			var iconClass;
			if (item.end_of_life) {
				iconClass = 'appEndOfLifeIcon';
			} else if (item.update_available) {
				iconClass = 'appUpdateIcon';
			}
			if (item.installations) {
				tools.forIn(item.installations, function(server, info) {
					if (info.update_available) {
						iconClass = 'appUpdateIcon';
						return false;
					}
				});
			}
			return iconClass || this.inherited(arguments);
		},

		getItemStatusTooltipMessage: function(item) {
			var tooltipMessage;
			var statusIconClass = this.getStatusIconClass(item);
			if (statusIconClass.indexOf("EndOfLife") !== -1) {
				if (item.is_installed) {
					tooltipMessage = _('This application will not get any further updates. We suggest to uninstall %(app)s and search for an alternative application.', {app: item.name});
				} else {
					tooltipMessage = _("This application will not get any further updates.");
				}
			} else if (statusIconClass.indexOf('Update') !== -1) {
				tooltipMessage = _("Update available");
			}
			return tooltipMessage || this.inherited(arguments);
		}
	});
});
