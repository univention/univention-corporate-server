/*
 * Copyright 2011-2019 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"umc/dialog",
	"umc/tools",
	"umc/widgets/Page",
	"umc/widgets/ContainerWidget",
	"umc/widgets/TitlePane",
	"umc/i18n!umc/modules/admindiary"
], function(declare, lang, array, dialog, tools, Page, ContainerWidget, TitlePane, _) {
	return declare("umc.modules.admindiary.DetailsPage", [ Page ], {

		helpText: _('This module lists all entries of the Admin Diary. You may comment on the events.'),
		fullWidth: true,

		buildRendering: function() {
			this.inherited(arguments);
			this._container = new ContainerWidget({});
			this.addChild(this._container);
			this.startup();
		},

		reset: function(items) {
			this._container.destroyRecursive();
			this._container = new ContainerWidget({});
			this.addChild(this._container);
			array.forEach(items, lang.hitch(this, function(item) {
				var name = lang.replace(_('{event} on {date} (by {user})'), {
					'event': item.event,
					date: item.date,
					user: item.author,
				});
				var titlePane = new TitlePane({
					title: name
				});
				//titlePane.addChild(form);
				this._container.addChild(titlePane);
			}));
		},
	});
});
