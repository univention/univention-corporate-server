/*
 * Copyright 2011-2015 Univention GmbH
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
/*global define console window*/

// Mixin that establishes a kind of polling for changes.
//
// The idea behind is that the store can return a kind of 'serial'
// value that will change if the underlying data has changed.

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"umc/tools"
], function(declare, lang, tools) {
	return declare('umc.modules.updater._PollingMixin', [], {

		postMixinProperties: function() {
			this.inherited(arguments);
		},

		buildRendering: function() {

			this.inherited(arguments);

			// Everything needed is kept in the 'polling' dictionary: constructor arguments
			// and all private status variables.
			//
			//	{
			//		// ------------ fields expected by our constructor ----------------
			//
			//		'interval':			some milliseconds
			//		'query':			an UMCP command to obtain the serial
			//		'callback':			the function (a method of 'this') to call if something has changed
			//
			//		// -------- fields maintained while polling is active -------------
			//
			//		'value':			the last seen value of our serial
			//		'function':			the function that fires the query
			//		'handler':			the function that handles the query result
			//		'timer':			the handle to the timeout (avoids double invocation)
			//	}
			//
			// All calls are wrapped into try/catch blocks. Errors cause a console error to be posted.
			// As we've set the 'handleErrors=false' flag, we can safely repeat the loop while errors
			// are encountered.
			//
			// If the class we're being mixed into contains the onQueryError() and onQuerySuccess() functions
			// then they'll be called whenever a query returns.
			if (this.polling)
			{
				tools.assert(this.polling.interval,	"_PollingMixin does not work without 'interval' argument.");
				tools.assert(this.polling.query,		"_PollingMixin does not work without 'query' argument.");
				tools.assert(this.polling.callback,	"_PollingMixin does not work without 'callback' argument.");

				this.polling.value = 0;		// initial values.
				this.polling.timer = '';

				// 'function' starts UMCP command and hands result over to 'handler'
				this.polling['function'] = lang.hitch(this, function() {
					try
					{
						tools.umcpCommand(this.polling.query,{},false).then(
							lang.hitch(this,function(data) {
								this.onQuerySuccess(this.polling.query);
								this.polling.handler(data);
							}),
							lang.hitch(this,function() {
								this.onQueryError(this.polling.query.data);
								this.polling.handler(null);
							})
							);
					}
					catch(error)
					{
						console.error("Polling [function] error: " + error.message);
					}
				});

				// 'handler' checks for changedness, calls callback and reschedules 'function'
				this.polling.handler = lang.hitch(this, function(data) {
					try
					{
						if (data !== null)
						{
							if (data.result != this.polling.value)
							{
								this.polling.value = data.result;
								this.polling.callback();
							}
						}
						// on errors: reset the last seen value, so we ensure the next
						// sucessful callback will trigger the 'callback()' event.
						else
						{
							this.polling.value = 0;
						}
						if ((this.polling.interval) && (! this.polling.timer))
						{
							this.polling.timer = window.setTimeout(lang.hitch(this,function() {
								this.polling.timer = '';
								this.polling['function']();
							}),this.polling.interval);
						}
					}
					catch(error)
					{
						console.error("Polling [handler] error: " + error.message);
					}
				});

				this.startPolling();
			}
		},

		// public function to start polling
		startPolling: function() {
			if ((this.polling) && (this.polling.handler) && (typeof(this.polling.handler) == 'function'))
			{
				this.polling.handler(null);
			}
		},

		// public function to stop polling
		stopPolling: function() {
			if (this.polling)
			{
				this.polling.interval = 0;
			}
		},

		// stops the timer if the object is destroyed.
		uninitialize: function() {

			this.stopPolling();
			this.inherited(arguments);
		}

	});
});
