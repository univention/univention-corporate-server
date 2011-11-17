/*
 * Copyright 2011 Univention GmbH
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
/* global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules.mrtg");

dojo.require("umc.i18n");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Module");
dojo.require("umc.widgets.Page");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.ExpandingTitlePane");
dojo.require("umc.widgets.ContainerForm");
dojo.require("umc.widgets.TabbedModule");
dojo.require("dojox.layout.TableContainer");
dojo.require("dojox.string.sprintf");

// Inheriting from umc.widgets.TabbedModule so any pages being added
// will become tabs automatically.
dojo.declare("umc.modules.mrtg", [ umc.widgets.TabbedModule, umc.i18n.Mixin ], {

	_page: null,
	_form: null,
	
	// TODO should be set in the base class -> then remove it here.
	nested: true,		// my tabs are 2nd level

	i18nClass: 'umc.modules.mrtg',

	buildRendering: function() {
		this.inherited(arguments);
		
		// key ...... the file name stub for all images on this tab
		// label .... the label of the tab itself
		// heading .. page heading of the tab contents
		// desc ..... help text (switchable)
		var page_setup = [
			{
				key:		"0load",
				label:		this._("Load"),
				heading:	this._("System load"),
				desc:		this._("System load in percent")
			},
			{
				key:		"1sessions",
				label:		this._("Sessions"),
				heading:	this._("Terminal server sessions"),
				desc:		this._("Number of active terminal server sessions")
			},
			{
				key:		"2mem",
				label:		this._("Memory"),
				heading:	this._("Memory usage"),
				desc:		this._("Utilization of system memory in percent")
			},
			{
				key:		"3swap",
				label:		this._("Swap"),
				heading:	this._("Swap space"),
				desc:		this._("Utilization of swap space in percent")
			}
		];
		
		// key ...... file name stub (2nd part) for the corresponding PNG image
		// label .... how to label this image
		var tab_setup = [
			{
				key:		"day",
				label:		this._("Previous day")
			},
			{
				key:		"week",
				label:		this._("Previous week")
			},
			{
				key:		"month",
				label:		this._("Previous month")
			},
			{
				key:		"year",
				label:		this._("Previous year")
			}
		];

		// Build tabs and attach them to page
		for (var idx=0; idx<page_setup.length; idx++)
		{
			var tab = new umc.widgets.Page({
				title:			page_setup[idx].label,
				headerText:		page_setup[idx].heading,
				closable:		false
				});
			this.addChild(tab);

			// Title pane without rollup/down
			var cont = new umc.widgets.ExpandingTitlePane({
				title:			page_setup[idx].desc
			});
			tab.addChild(cont);
			
			// ExpandingTitlePane doesn't honor 'scrollable'
			// but we might need it
			var scroll = new umc.widgets.ContainerWidget({
				scrollable:		true
			});
			cont.addChild(scroll);
			
			// three-column grid layout
			var grid = new dojox.layout.TableContainer({
				cols: 3
			});
			scroll.addChild(grid);
			for (var i=0; i<tab_setup.length; i++)
			{
				grid.addChild(new dijit.layout.ContentPane({
					content: 	dojox.string.sprintf(
									"<span style='white-space:nowrap;'>%s</span>",
									tab_setup[i].label)
				}));
				grid.addChild(new dijit.layout.ContentPane({
					content:	dojox.string.sprintf(
									"<img src='/statistik/ucs_%s-%s.png'>",
									page_setup[idx].key,
									tab_setup[i].key)
				}));
				// third column used as spacer
				grid.addChild(new dijit.layout.ContentPane({
					content:	'&nbsp;'
				}));
			}
		}
	}	
});
