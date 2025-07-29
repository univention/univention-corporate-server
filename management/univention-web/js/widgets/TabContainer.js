/*
 * SPDX-FileCopyrightText: 2011-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/dom-class",
	"dojo/topic",
	"dijit/layout/TabContainer",
	"umc/tools",
	"umc/i18n!"
], function(declare, lang, array, domClass, topic, TabContainer, tools, _) {
	return declare("umc.widgets.TabContainer", TabContainer, {
		// summary:
		//		An extended version of the dijit TabContainer that can hide/show tabs.

		_parentModule: undefined,

		_setVisibilityOfChild: function( child, visible ) {
			tools.assert( child.controlButton !== undefined, 'The widget is not attached to a TabContainer' );
			// we iterate over the children of the container to ensure the given widget is attached to THIS TabContainer
			array.forEach( this.getChildren(), function( item ) {
				if ( item == child ) {
					domClass.toggle( item.controlButton.domNode, 'dijitDisplayNone', ! visible );
					return false;
				}
			} );
		},

		buildRendering: function() {
			this.inherited(arguments);
			this.watch('selectedChildWidget', lang.hitch(this, function(name, oldPage, newPage) {
				// publish action event when subtab changes
				// ... first get the enclosing parental module
				if (this._parentModule === undefined) {
					this._parentModule = tools.getParentModule(this);
				}
				if (!this._parentModule) {
					// could not determine our parent module
					return;
				}

				// inverse the localized subtab title
				var title = _.inverse(newPage.title, 'umc/modules/' + this._parentModule.moduleID);
				topic.publish('/umc/actions', this._parentModule.moduleID, this._parentModule.moduleFlavor, 'subtab', title);
			}));
		},

		hideChild: function( child ) {
			this._setVisibilityOfChild( child, false );
		},

		showChild: function( child ) {
			this._setVisibilityOfChild( child, true );
		}
	});
});
