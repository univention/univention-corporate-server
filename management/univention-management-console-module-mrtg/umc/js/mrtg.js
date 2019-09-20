/*
 * Copyright 2011-2019 Univention GmbH
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
	"dojox/html/entities",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/TabbedModule",
	"umc/i18n!umc/modules/mrtg"
], function(declare, lang, array, entities, Page, Text, TabbedModule, _) {
	return declare("umc.modules.mrtg", TabbedModule, {

		_page: null,
		_form: null,
		
		buildRendering: function() {
			this.inherited(arguments);
			
			// key ...... the file name stub for all images on this tab
			// title... the title of the tab itself
			// desc ..... help text (switchable)
			var page_setup = [{
				key: "0load",
				title: _("System load"),
				desc: _("System load in percent")
			}, {
				key: "2mem",
				title: _("Memory usage"),
				desc: _("Utilization of system memory in percent")
			}, {
				key: "3swap",
				title: _("Swap space"),
				desc: _("Utilization of swap space in percent")
			}];
			
			// key ...... file name stub (2nd part) for the corresponding PNG image
			// label .... how to label this image
			var tab_setup = [ {
				key: "day",
				label: _("Previous day")
			}, {
				key: "week",
				label: _("Previous week")
			}, {
				key: "month",
				label: _("Previous month")
			}, {
				key: "year",
				label: _("Previous year")
			}];

			// Build tabs and attach them to page
			array.forEach(page_setup, lang.hitch(this, function(page) {
				var child= new Page({
					title: page.title,
					headerText: page.desc,
					headerTextRegion: 'main',
					closable: false
				});
				this.addTab(child);

				array.forEach(tab_setup, function(tab) {
					child.addChild(new Text({
						content: lang.replace('<h3>{0}</h3><img src="/univention/command/mrtg/statistic/get?filename=ucs_{1}-{2}.png">', [entities.encode(tab.label), entities.encode(encodeURIComponent(page.key)), entities.encode(encodeURIComponent(tab.key))])
					}));
				});
			}));
		}
	});
});
