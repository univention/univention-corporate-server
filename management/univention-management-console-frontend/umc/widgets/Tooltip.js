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
/*global dojo dijit dojox umc console setTimeout */

dojo.provide("umc.widgets.Tooltip");

dojo.require("dijit.Tooltip");
dojo.require("umc.tools");

/*dojo.extend(dijit._MasterTooltip, {
	buildRendering: function() {
		if(!this.domNode){
			// Create root node if it wasn't created by _Templated
			this.domNode = this.srcNodeRef || dojo.create('div');
		}

		// hide the tooltip
		this.connect(this.domNode, 'onclick', 'hide');
	}
});*/

// connect to the master tooltip's domNode onlick event in order to
// trigger the fade out animation.
(function() {
	// this does not work correctly, only hides tooltip once
	//var hdl = dojo.connect(dijit, 'showTooltip', function(innerHTML, aroundNode) {
	//	dojo.connect(dijit._masterTT.domNode, 'onclick', dojo.hitch(dijit._masterTT, 'hide', aroundNode));
	var hdl = dojo.connect(dijit, 'showTooltip', function() {
		dojo.connect(dijit._masterTT.domNode, 'onclick', dijit._masterTT.fadeOut, 'play');

		// disconnect from 'showTooltip', we only need to register the handler once
		dojo.disconnect(hdl);
	});
})();

dojo.declare("umc.widgets.Tooltip", dijit.Tooltip, {
	// the widget's class name as CSS class
	'class': 'umcTooltip',

	_onHover: function(/*Event*/ e) {
		// only show the tooltip if the config cookie for this is not set or set to 'true'
		if (umc.tools.preferences('tooltips')) {
			this.inherited(arguments);
		}
	}

});


