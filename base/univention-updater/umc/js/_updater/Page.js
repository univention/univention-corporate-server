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

dojo.provide("umc.modules._updater.Page");

dojo.require("umc.i18n");
dojo.require("umc.widgets.TabbedModule");
dojo.require("umc.widgets.StandbyMixin");


// Page with some useful additions:
//
//	-	add the ability to change helpText and headerText
//	-	add a prototype for a refresh function
//
dojo.declare("umc.modules._updater.Page", [
	umc.widgets.Page,
    umc.widgets.StandbyMixin,
	umc.i18n.Mixin
	] ,
{
	buildRendering: function() {

		this.inherited(arguments);

		// helpText and headerText changeable
		this.watch('headerText',dojo.hitch(this,function(name,oldval,newval) {
			var children = this.getChildren();
			// the header text element is (currently) not a member variable,
			// so I have to search for the one element that has region='top'
			for (var ch in children)
			{
				if (children[ch].get('region') == 'top')
				{
					children[ch].set('content','<h1>' + newval + '</h1>');
					return;
				}
			}
		}));
		this.watch('helpText',dojo.hitch(this,function(name,oldval,newval) {
			this._helpTextPane.set('content',newval);
		}));
	},

	// should be overloaded by subclasses that need an entry point
	// that should reload/refresh changed data and update the display
	refreshPage: function() {
	},

	// can be listened to by instances that want to be notified
	// if something on this page has changed. Does not propagate
	// any args or current data.
	dataChanged: function() {
	},

	startup: function() {

		this.inherited(arguments);

		// Establish generic listeners for all of our direct children.
		var ch = this.getChildren();
		for (var i in ch)
		{
			dojo.connect(ch[i],'_query_error',dojo.hitch(this, function(subject,data) {
				this._query_error(subject,data);
			}));
			dojo.connect(ch[i],'_query_success',dojo.hitch(this, function(subject) {
				this._query_success(subject);
			}));
		}
	},

	// Two callbacks that are used by queries that want to propagate
	// their outcome to the main error handlers
	_query_error: function(subject,data) {
	},
	_query_success: function(subject) {
	}
});
