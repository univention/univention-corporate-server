/*
 * SPDX-FileCopyrightText: 2011-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/array",
	"dojo/dom-class",
	"dijit/TitlePane",
	"dijit/_Container",
	"dojox/grid/_Grid",
	"./Icon",
	"put-selector/put"
], function(declare, array, domClass, TitlePane, _Container, _Grid, Icon, put) {
	return declare("umc.widgets.TitlePane", [ TitlePane, _Container ], {
		// summary:
		//		Widget that extends dijit.TitlePane with methods of a container widget.

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'umcTitlePane');
			var icon = new Icon({
				'class': 'umcTitlePaneTitleFocus__arrowIcon',
				iconName: 'chevron-down'
			});
			put(this.focusNode, icon.domNode);
		},

		startup: function() {
			this.inherited(arguments);

			array.forEach(this.getChildren(), function(ichild) {
				if (ichild.startup && !ichild._started) {
					ichild.startup();
				}
			});


			// FIXME: Workaround for refreshing problems with datagrids when they are rendered
			//        in a closed TitlePane

			// iterate over all tabs
			array.forEach(this.getChildren(), function(iwidget) {
				if (iwidget.isInstanceOf(_Grid)) {
					// hook to changes for 'open'
					this.own(this.watch('open', function(attr, oldVal, newVal) {
						if (newVal) {
							// recall startup when the TitelPane gets shown
							iwidget.startup();
						}
					}));
				}
			}, this);
		}
	});
});

