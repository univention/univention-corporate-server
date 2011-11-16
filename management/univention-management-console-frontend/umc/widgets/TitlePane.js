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
/*global dojo dijit dojox umc console window */

dojo.provide("umc.widgets.TitlePane");

dojo.require("dijit.TitlePane");
dojo.require("dijit._Container");

dojo.declare("umc.widgets.TitlePane", [ dijit.TitlePane, dijit._Container ], {
	// summary:
	//		Widget that extends dijit.TitlePane with methods of a container widget.

	// the widget's class name as CSS class
	'class': 'umcTitlePane',

	startup: function() {
		this.inherited(arguments);

		// FIXME: Workaround for refreshing problems with datagrids when they are rendered
		//        in a closed TitlePane

		// iterate over all tabs
		dojo.forEach(this.getChildren(), function(ipage) {
			// find all widgets that inherit from dojox.grid._Grid on the tab
			dojo.forEach(ipage.getDescendants(), function(iwidget) {
				if (umc.tools.inheritsFrom(iwidget, 'dojox.grid._Grid')) {
					// hook to changes for 'open'
					this.watch('open', function(attr, oldVal, newVal) {
						if (newVal) {
							// recall startup when the TitelPane gets shown
							iwidget.startup();
						}
					});
				}
			}, this);
		}, this);
	}
});


