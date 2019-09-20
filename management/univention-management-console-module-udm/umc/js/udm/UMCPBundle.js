/*
 * Copyright 2012-2019 Univention GmbH
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
	"dojo/_base/kernel",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/Deferred",
	"dojox/timing/_base"
], function(kernel, lang, array, Deferred, timing) {
	var UMCPBundle = function(command, umcpCommand) {
		this.command = command;
		this.umcpCommand = umcpCommand;
		this.timer = new timing.Timer(100); // 0.1 sec
		this.timer.onTick = lang.hitch(this, 'fetchAll');
		this.bundledParamsArray = [];
		this.deferreds = [];
	};

	kernel.extend(UMCPBundle, {
		fetchAll: function() {
			this.timer.stop();
			// local copy
			var bundledParamsArray = this.bundledParamsArray;
			var deferreds = this.deferreds;
			// clear arrays: be ready to fill them again
			this.bundledParamsArray = [];
			this.deferreds = [];
			this.umcpCommand(this.command, bundledParamsArray).then(
				lang.hitch(this, function(data) {
					array.forEach(deferreds, function(deferred, i) {
						deferred.resolve({
							status: data.status,
							message: data.message,
							result: data.result[i]
						});
					});
				})
			);
		},

		addParams: function(params) {
			this.timer.stop();
			var sizeNewParams = 0;
			for (var key in params) {
				sizeNewParams++;
			}
			for (var i = 0; i < this.bundledParamsArray.length; i++) {
				var existingParams = this.bundledParamsArray[i];
				var sizeExistingParams = 0;
				var valuesEqual = true;
				for (key in existingParams) {
					if (existingParams[key] !== params[key]) {
						valuesEqual = false;
						break;
					}
					sizeExistingParams++;
				}
				if (valuesEqual && sizeNewParams == sizeExistingParams) {
					this.timer.start();
					return this.deferreds[i];
				}
			}
			this.bundledParamsArray.push(params);
			var deferred = new Deferred();
			this.deferreds.push(deferred);
			this.timer.start();
			return deferred;
		}
	});

	return UMCPBundle;
});

