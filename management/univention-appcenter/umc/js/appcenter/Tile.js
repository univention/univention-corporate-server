/*
 * Copyright 2020-2022 Univention GmbH
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
	"dojo/_base/kernel",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/_base/event",
	"dijit/Tooltip",
	"dojo/on",
	"umc/tools",
	"dijit/_WidgetBase",
	"dijit/_TemplatedMixin",
	"umc/i18n!umc/modules/appcenter"
], function(declare, kernel, array, domClass, dojoEvent, Tooltip, on, tools, _WidgetBase, _TemplatedMixin, _) {
	return declare("umc.modules.appcenter.Tile", [_WidgetBase, _TemplatedMixin], {
		baseClass: 'umcTile',
		clickCallback: null,
		templateString: `
			<div>
				<div class="umcTile__selectionBox"></div>
				<div class="umcTile__inner">
					<div
						class="umcTile__box"
						style="background: \${bgc}"
					>
						<img
							class="umcTile__logo"
							src="\${logo}"
							alt="\${name} logo"
							onerror="this.src='/univention/management/modules/appcenter/icons/logo_fallback.svg'"
						>
						<div class="appStatusIcon" data-dojo-attach-point="statusNode" data-dojo-attach-event="onclick: _tooltip"></div>
					</div>
					<span class="umcTile__name">\${name}</span>
				</div>
			</div>
		`,
		_tooltip: function(evt) {
			var statusIconClass = this._getStatusIconClass();
			if (! statusIconClass) {
				return null;
			}
			var tooltipMessage;
			if (statusIconClass.indexOf("EndOfLife") !== -1) {
				if (this.obj.isInstalled) {
					tooltipMessage = _('This application will not get any further updates. We suggest to uninstall %(app)s and search for an alternative application.', {app: this.obj.name});
				} else {
					tooltipMessage = _("This application will not get any further updates.");
				}
			} else if (statusIconClass.indexOf('Update') !== -1) {
				tooltipMessage = _("Update available");
			} else if (statusIconClass.indexOf('VoteForApp') !== -1) {
				tooltipMessage = _('Vote for this app now and bring your favorite faster to the Univention App Center');
			} else if (statusIconClass == 'appRecommendedAndPopularAppIcon') {
				tooltipMessage = array.filter(this.obj.rating, function(irating) {
					return irating.name === 'RecommendedApp';
				})[0].description;
				tooltipMessage += '<br><br>';
				tooltipMessage += array.filter(this.obj.rating, function(irating) {
					return irating.name === 'PopularityAward';
				})[0].description;
			} else if (statusIconClass == 'appRecommendedAppIcon') {
				tooltipMessage = array.filter(this.obj.rating, function(irating) {
					return irating.name === 'RecommendedApp';
				})[0].description;
			} else if (statusIconClass == 'appPopularAppIcon') {
				tooltipMessage = array.filter(this.obj.rating, function(irating) {
					return irating.name === 'PopularityAward';
				})[0].description;
			}
			if (! tooltipMessage) {
				return null;
			}
			var node = evt.target;
			Tooltip.show(tooltipMessage, node);
			if (evt) {
				dojoEvent.stop(evt);
			}
			on.once(kernel.body(), 'click', function(evt) {
				Tooltip.hide(node);
				dojoEvent.stop(evt);
			});
		},
		_upgradeAvaiable() {
			var updateAvailable = this.obj.canUpgrade();
			if (this.domainWide) {
				updateAvailable = updateAvailable || this.obj.canUpgradeInDomain();
			}
			return updateAvailable;
		},
		_getStatusIconClass: function() {
			if (! this.obj) {
				return null;
			}
			var iconClass;
			if (this.obj.endOfLife) {
				iconClass = 'appEndOfLifeIcon';
			} else if (this.obj.voteForApp) {
				iconClass = 'appVoteForApp';
			} else if (this._upgradeAvaiable()) {
				if (this.obj.candidateHasNoInstallPermissions) {
					iconClass = 'appUpdatePermissionsIcon';
				} else {
					iconClass = 'appUpdateIcon';
				}
			} else {
				var isRecommendedApp = array.some(this.obj.rating, function(iRating) {
					return iRating.name === 'RecommendedApp';
				});
				var isPopularApp = array.some(this.obj.rating, function(iRating) {
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
			return iconClass;
		},
		postCreate: function() {
			this.inherited(arguments);
			var statusIconClass = this._getStatusIconClass();
			if (statusIconClass) {
				domClass.add(this.statusNode, statusIconClass);
			} else {
				domClass.add(this.statusNode, 'dijitDisplayNone');
			}
		},
		_setVisibleAttr: function(newVal) {
			this._set('visible', newVal);
			domClass.toggle(this.domNode, 'dijitDisplayNone', !newVal);
		}
	});
});
