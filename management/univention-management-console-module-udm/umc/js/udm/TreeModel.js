/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojox/string/sprintf",
	"umc/tools"
], function(declare, lang, array, sprintf, tools) {
	return declare('umc.modules.udm.TreeModel', null, {
		// summary:
		//		Class that implements the tree model for the UDM container hierarchy.
		// summary:
		//		This class that implements a tree model for the container hierarchy which
		//		is use in the UDM navigation module in combination with the diji.Tree widget.
		//		More details about this model can be found in dijit.tree.model.

		// umcpCommand: Function
		//		Reference to the module specific umcpCommand function.
		umcpCommand: null,
		moduleFlavor: null,

		command: 'udm/nav/container/query',

		root: null,

		constructor: function(args) {
			lang.mixin(this, args);
		},

		getRoot: function(onItem) {
			this.umcpCommand(this.command).then(lang.hitch(this, function(data) {
				var results = data.result instanceof Array ? data.result : [];
				if (results.length) {
					this.root = results[0];
					onItem(results[0]);
				}
				else {
					console.log('WARNING: No top container could be queried for LDAP navigation! Ignoring error.');
				}
			}));
		},

		getLabel: function(item) {
			return item.label;
		},

		mayHaveChildren: function(item) {
			return item.$childs$;
		},

		getIdentity: function(item) {
			return item.id;
		},

		getChildren: function(parentItem, onComplete) {
			this.umcpCommand(this.command, { container: parentItem.id }).then(lang.hitch(this, function(data) {
				// sort items alphabetically
				var results = data.result instanceof Array ? data.result : [];
				results = array.map(results, lang.hitch(this, function(obj) {
					obj.sortlabel = obj.label;
					if (obj.objectType === 'dns/reverse_zone') {
						// sort IP's numerical
						if (~obj.label.indexOf(':')) {
							// ipv6
							obj.sortlabel = array.map(obj.label.split(':'), function(v) { return sprintf('%05d', parseInt(v, 16)); }).join(':');
						} else {
							// ipv4
							obj.sortlabel = array.map(obj.label.split('.'), function(v) { return sprintf('%03d', v); }).join('.');
						}
					}
					return obj;
				}));
				if (this.moduleFlavor !== 'navigation') {
					results.sort(tools.cmpObjects('objectType', 'sortlabel'));
				} else {
					results.sort(tools.cmpObjects('label'));
				}
				try {
					onComplete(results);
				} catch (error) {
					// don't do anything
				}
			}), lang.hitch(this, function() {
				try {
					onComplete([]);
				} catch (error) {
					// don't do anything
				}
			}));
		}
	});
});
