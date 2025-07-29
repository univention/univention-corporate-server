/*
 * SPDX-FileCopyrightText: 2017-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
		'master': _('Primary Directory Node'),
		'backup': _('Backup Directory Node'),
		'slave': _('Replica Directory Node'),
		'member': _('Managed Node')
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

