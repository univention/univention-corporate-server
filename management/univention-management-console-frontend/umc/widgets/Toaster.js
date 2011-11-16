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
/*global dojo dijit dojox umc console */

dojo.provide("umc.widgets.Toaster");

dojo.require("dojox.widget.Toaster");

// TODO: the css property box-shadow does not work since a clipping is set dynamically,
//		 this could be fixed...
dojo.declare("umc.widgets.Toaster", dojox.widget.Toaster, {
	// summary:
	//		Extension of dojox.widget.Toaster in order to allow centered notification.

	// positionDirection: String
	//		Position from which message slides into screen, one of
	//		["br-up", "br-left", "bl-up", "bl-right", "tr-down", "tr-left", "tl-down", "tl-right"]
	positionDirection: "tc-down",

	// positionDirectionTypes: Array
	//		Possible values for positionDirection parameter
	positionDirectionTypes: ["br-up", "br-left", "bc-up", "bl-up", "bl-right", "tr-down", "tr-left", "tc-down", "tl-down", "tl-right"],

	// extend internal method for placing elements
	_placeClip: function() {
		//TODO: Could be made smarter for the case the clip is displayed somewhere 
		//      else than the top center.
		this.inherited(arguments);

		// get the viewport and node size
		var view = dojo.window.getBox();
		var nodeSize = dojo.marginBox(this.containerNode);

		// set up the position for a centered toaster
		var style = this.clipNode.style;
		var pd = this.positionDirection;
		if(pd.match(/^[tb]c-/)){
			style.left = ((view.w - nodeSize.w) / 2 - view.l - 5)+"px";
			style.height = (nodeSize.h+5)+"px";
			style.width = (nodeSize.w+10)+"px";
		}

		// redo the clipping
		style.clip = "rect(0px, " + (nodeSize.w + 10) + "px, " + (nodeSize.h + 5) + "px, -5px)";
	},

	setContent: function(/*String|Function*/message, /*String*/messageType, /*int?*/duration) {
		//TODO: Could be made smarter for the case the clip is displayed somewhere 
		//      else than the top center.
		this.inherited(arguments);

		var style = this.containerNode.style;
		style.left = '5px';
		this.slideAnim.stop();
		this.slideAnim.properties.left = 5;
		this.slideAnim.play();
	}

});



