/*
 * Copyright 2011-2012 Univention GmbH
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
/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._updater.Grid");

dojo.require("umc.widgets.Grid");
dojo.require("umc.modules._updater._PollingMixin");

// Grid with some useful additions:
//
//	-	add capability to poll for changes in the store, and
//		to refresh the whole grid if something has changed.
//
dojo.declare("umc.modules._updater.Grid", [
	umc.widgets.Grid,
	umc.modules._updater._PollingMixin
	],
{
	buildRendering: function() {
		
		this.inherited(arguments);
		
	},
	
	// Two callbacks that are used by queries that want to propagate
	// their outcome to the main error handlers
	_query_error: function(subject,data) {
	},
	_query_success: function(subject) {
	}
});
