/*
 * Copyright 2020 Univention GmbH
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
/*global define, require*/

define([
	"dojo/_base/lang",
	"dojo/Deferred",
	"umc/render",
	"umc/widgets/Standby",
	"./portalContent"
], function(lang, Deferred, render, Standby, portalContent) {
	return {
		_udmCache() {
			const deferred = new Deferred();
			require(['umc/modules/udm/cache'], (cache) => {
				deferred.resolve(cache.get('portals/all'));
			});
			return deferred;
		},

		getFormConf: async function(type, propNames, dn) {
			const moduleCache = await this._udmCache();
			const moduleStore = portalContent.udmStore();
			let widgets = await moduleCache.getProperties(type);
			widgets = lang.clone(widgets)
				.filter(prop => propNames.includes(prop.id))
				.map(prop => {
					if (prop.id === 'portalComputers') {
						prop.type = 'umc/modules/udm/MultiObjectSelect';
						prop.umcpCommand = moduleStore.umcpCommand;
					}
					if (dn && (prop.readonly || !prop.editable)) {
						prop.disabled = true;
					}
					return prop;
				});
			await render.requireWidgets(widgets);
			return {
				widgets,
				layout: propNames,
				moduleStore,
			};
		},
	};
});
