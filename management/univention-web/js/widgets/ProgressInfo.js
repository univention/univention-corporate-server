/*
 * SPDX-FileCopyrightText: 2012-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define*/

define([
	"dojo/_base/declare",
	"dijit/ProgressBar",
	"umc/widgets/ContainerWidget",
	"umc/widgets/Text"
], function(declare, ProgressBar, ContainerWidget, Text) {
	return declare("umc.widgets.ProgressInfo", ContainerWidget, {
		// summary:
		//		widget used displaying progress information
		baseClass: 'umcProgressInfo',

		_titleWidget: null,

		_infoWidget: null,

		_progressBar: null,

		maximum: 100,

		current: 0,

		buildRendering: function() {
			this.inherited(arguments);

			// setup a progress bar with some info text
			this._titleWidget = new Text( {
				content: ''
			} );
			this._infoWidget = new Text( {
				content: ''
			} );
			this._progressBar = new ProgressBar({});
			this.addChild( this._titleWidget );
			this.addChild( this._progressBar );
			this.addChild( this._infoWidget );

			this.startup();
		},

		updateTitle: function( title ) {
			if ( title !== undefined ) {
				this._titleWidget.set( 'content', title );
			}
		},

		updateInfo: function( information ) {
			if ( information !== undefined ) {
				this._infoWidget.set( 'content', information );
			}
		},

		update: function( value, information, title ) {
			if ( value === 0 ) {
				// initiate the progressbar and start the standby
				this._progressBar.set( 'maximum', this.maximum );
				this._progressBar.set( 'value', 0 );
			} else if ( value >= this.maximum || value < 0 ) {
				// finish the progress bar
				this._progressBar.set( 'value', this.maximum );
			} else {
				this._progressBar.set( 'value', value );
			}
			this.updateInfo( information );
			this.updateTitle( title );
		}
	});
});
