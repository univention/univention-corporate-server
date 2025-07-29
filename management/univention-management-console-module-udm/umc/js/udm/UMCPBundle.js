/*
 * SPDX-FileCopyrightText: 2012-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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

