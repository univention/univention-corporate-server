/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
	"umc/widgets/Page"
], function(declare, lang, array, Page) {
	return declare("umc.modules.updater.Page", [ Page ] , {
		// should be overloaded by subclasses that need an entry point
		// that should reload/refresh changed data and update the display
		refreshPage: function() {
		},

		startup: function() {

			this.inherited(arguments);

			// Establish generic listeners for all of our direct children.
			var children = this.getChildren();
			array.forEach(children, lang.hitch(this, function(child) {
				child.on('queryerror', lang.hitch(this, 'onQueryError'));
				child.on('querysuccess', lang.hitch(this, 'onQuerySuccess'));
			}));
		},

		// Two callbacks that are used by queries that want to propagate
		// their outcome to the main error handlers
		onQueryError: function(subject, data) {
		},
		onQuerySuccess: function(subject) {
		}
	});

});
