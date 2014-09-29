/*
 * Copyright 2011-2014 Univention GmbH
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
	"dijit/layout/ContentPane",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Page",
	"umc/widgets/Text",
	"umc/widgets/TabbedModule",
	"dojox/layout/TableContainer",
	"dojox/string/sprintf",
	"umc/i18n!umc/modules/mrtg"
], function(declare, lang, array, DijitContentPane, ContainerWidget, Page, Text, TabbedModule, TableContainer, sprintf, _) {
	return declare("umc.modules.mrtg", TabbedModule, {

		_page: null,
		_form: null,
		
		buildRendering: function() {
			this.inherited(arguments);
			
			// key ...... the file name stub for all images on this tab
			// title... the title of the tab itself
			// desc ..... help text (switchable)
			var page_setup = [{
				key:		"0load",
				title:	_("System load"),
				desc:		_("System load in percent")
			}, {
				key:		"1sessions",
				title:	_("Terminal server sessions"),
				desc:		_("Number of active terminal server sessions")
			}, {
				key:		"2mem",
				title:	_("Memory usage"),
				desc:		_("Utilization of system memory in percent")
			}, {
				key:		"3swap",
				title:	_("Swap space"),
				desc:		_("Utilization of swap space in percent")
			}];
			
			// key ...... file name stub (2nd part) for the corresponding PNG image
			// label .... how to label this image
			var tab_setup = [ {
				key:		"day",
				label:		_("Previous day")
			}, {
				key:		"week",
				label:		_("Previous week")
			}, {
				key:		"month",
				label:		_("Previous month")
			}, {
				key:		"year",
				label:		_("Previous year")
			}];

			// Build tabs and attach them to page
			array.forEach(page_setup, lang.hitch(this, function(page) {
				var tab = new Page({
					title: page.title,
					closable: false
				});
				this.addTab(tab);

				tab.addChild(new Text({
					content: lang.replace('<h1>{0}</h1>', [page.desc]),
					'class': 'umcPageHeader',
					style: 'text-align: center'
				}));

				// three-column grid layout
				var grid = new TableContainer({
					cols: 3
				});
				tab.addChild(grid);

				array.forEach(tab_setup, function(tab) {
					grid.addChild(new DijitContentPane({
						content: sprintf("<span style='white-space:nowrap;'>%s</span>", tab.label)
					}));
					grid.addChild(new DijitContentPane({
						content: sprintf("<img src='/statistik/ucs_%s-%s.png'>", page.key, tab.key)
					}));
					// third column used as spacer
					grid.addChild(new DijitContentPane({
						content: '&nbsp;'
					}));
				});
			}));
		}
	});
});
