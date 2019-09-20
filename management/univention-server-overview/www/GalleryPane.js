/*
 * Copyright 2017-2019 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-construct",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/GalleryPane",
	"umc/i18n!server-overview"
], function(declare, lang, array, domConstruct, entities, tools, GalleryPane, _) {
	var roleLabels = {
		'master': _('DC master'),
		'backup': _('DC backup'),
		'slave': _('DC slave'),
		'member': _('Member server')
	};

	function getServerLabel(item) {
		if (item.serverRole instanceof Array) {
			return roleLabels[item.serverRole[0]];
		}
		return _('Unknown');
	}

	return declare([GalleryPane], {
		useFqdn: true,

		renderRow: function(item, options) {
			var getHostAddress = lang.hitch(this, function() {
				if (!this.useFqdn && item.ip instanceof Array && item.ip.length > 0) {
					return item.ip[0];
				}
				if (item.domain) {
					return lang.replace('{hostname}.{domain}', item);
				}
				return item.hostname;
			});

			var getVersion = function() {
				if (item.version) {
					return lang.replace('UCS {version}', item);
				}
				return '';
			};

			return domConstruct.toDom(lang.replace(
				'<div class="umcGalleryWrapperItem col-xxs-12 col-xs-6 col-sm-4 col-md-3 col-lg-3">' +
					'<a href="//{url}">' +
						'<div class="umcGalleryItem">' +
							'<div class="umcGalleryName">{name}</div>' +
							'<div class="umcGalleryDescription">{description}</div>' +
							'<div class="umcGalleryVersion">{version}</div>' +
						'</div>' +
					'</a>' +
				'</div>', {
				name: entities.encode(item.hostname),
				description: entities.encode(getServerLabel(item)),
				version: entities.encode(getVersion()),
				url: entities.encode(getHostAddress())
			}));
		},

		updateQuery: function(_pattern) {
			// allow wild cards
			_pattern = _pattern.replace(/\*/g, '.*');
			var pattern = new RegExp(_pattern, 'i');

			this.set('query', function(obj) {
				var result = false;
				tools.forIn(obj, function(ikey, ival) {
					if (typeof ival == 'string') {
						result = pattern.test(ival);
					}
					else if (ival instanceof Array) {
						result = array.some(ival, function(jval) {
							return pattern.test(jval);
						});
					}
					if (result) {
						// we found a match... break the loop
						return false;
					}
				});
				return result;
			});
		}
	});
});

