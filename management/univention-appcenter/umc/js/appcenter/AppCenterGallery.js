/*
 * Copyright 2013-2019 Univention GmbH
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
	"dojo/_base/array",
	"dojo/dom-class",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/AppGallery",
	"umc/i18n!umc/modules/appcenter"
], function(declare, array, domClass, entities, tools, AppGallery, _) {
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
			} else if (item.vote_for_app) {
				iconClass = 'appVoteForApp';
			} else if (item.update_available || this._update_available_in_domain(item)) {
				if (item.candidate_needs_install_permissions) {
					iconClass = 'appUpdatePermissionsIcon';
				} else {
					iconClass = 'appUpdateIcon';
				}
			} else {
				var isRecommendedApp = array.some(item.rating, function(iRating) {
					return iRating.name === 'RecommendedApp';
				});
				var isPopularApp = array.some(item.rating, function(iRating) {
					return iRating.name === 'PopularityAward';
				});
				if (isRecommendedApp && isPopularApp) {
					iconClass = 'appRecommendedAndPopularAppIcon';
				} else if (isRecommendedApp) {
					iconClass = 'appRecommendedAppIcon';
				} else if (isPopularApp) {
					iconClass = 'appPopularAppIcon';
				}
			}
			return iconClass || this.inherited(arguments);
		},

		_update_available_in_domain: function(item) {
			var updates_available_in_domain = false;
			if (item.installations) {
				tools.forIn(item.installations, function(server, info) {
					if (info.update_available) {
						updates_available_in_domain = true;
					}
				});
			}
			return updates_available_in_domain;
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
			} else if (statusIconClass.indexOf('VoteForApp') !== -1) {
				tooltipMessage = _('Vote for this app now and bring your favorite faster to the Univention App Center');
			} else if (statusIconClass == 'appRecommendedAndPopularAppIcon') {
				tooltipMessage = array.filter(item.rating, function(irating) {
					return irating.name === 'RecommendedApp';
				})[0].description;
				tooltipMessage += '<br><br>';
				tooltipMessage += array.filter(item.rating, function(irating) {
					return irating.name === 'PopularityAward';
				})[0].description;
			} else if (statusIconClass == 'appRecommendedAppIcon') {
				tooltipMessage = array.filter(item.rating, function(irating) {
					return irating.name === 'RecommendedApp';
				})[0].description;
			} else if (statusIconClass == 'appPopularAppIcon') {
				tooltipMessage = array.filter(item.rating, function(irating) {
					return irating.name === 'PopularityAward';
				})[0].description;
			}
			return tooltipMessage || this.inherited(arguments);
		}
	});
});
