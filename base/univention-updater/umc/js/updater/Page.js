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
/*global define*/


// Page with some useful additions:
//
//	-	add the ability to change helpText and headerText
//	-	add a prototype for a refresh function
//
define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/aspect",
	"umc/widgets/Page",
	"umc/widgets/StandbyMixin"
], function(declare, lang, array, aspect, Page, StandbyMixin) {
	return declare("umc.modules.updater.Page", [ Page, StandbyMixin ] , {
		buildRendering: function() {

			this.inherited(arguments);

			// helpText and headerText changeable
			this.watch('headerText', lang.hitch(this, function(name, oldval, newval) {
				var children = this.getChildren();
				// the header text element is (currently) not a member variable,
				// so I have to search for the one element that has region='top'
				array.forEach(children, function(child) {
					if (child.get('region') == 'top') {
						child.set('content', '<h1>' + newval + '</h1>');
						return;
					}
				});
			}));
			this.watch('helpText', lang.hitch(this, function(name, oldval, newval) {
				this._helpTextPane.set('content', newval);
			}));
		},

		// should be overloaded by subclasses that need an entry point
		// that should reload/refresh changed data and update the display
		refreshPage: function() {
		},

		startup: function() {

			this.inherited(arguments);

			// Establish generic listeners for all of our direct children.
			var children = this.getChildren();
			array.forEach(children, lang.hitch(this, function(child) {
				this.own(aspect.after(child, '_query_error', lang.hitch(this, function(subject, data) {
					this._query_error(subject, data);
				})));
				this.own(aspect.after(child, '_query_success', lang.hitch(this, function(subject) {
					this._query_success(subject);
				})));
			}));
		},

		// Two callbacks that are used by queries that want to propagate
		// their outcome to the main error handlers
		_query_error: function(subject, data) {
		},
		_query_success: function(subject) {
		}
	});

});
