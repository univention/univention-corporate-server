/*
 * Copyright 2012 Univention GmbH
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

dojo.provide("umc.widgets.ProgressInfo");

dojo.require("umc.widgets.ContainerWidget");
dojo.require("dijit.ProgressBar");

dojo.declare("umc.widgets.ProgressInfo", umc.widgets.ContainerWidget, {
	// summary:
	//		widget used displaying progress information

	_titleWidget: null,

	_infoWidget: null,

	_progressBar: null,

	maximum: 100,

	current: 0,

	buildRendering: function() {
		this.inherited(arguments);

		// setup a progress bar with some info text
		this._titleWidget = new umc.widgets.Text( {
			content: ''
		} );
		this._infoWidget = new umc.widgets.Text( {
			content: ''
		} );
		this._progressBar = new dijit.ProgressBar({
			'class' : 'umcProgressInfo'
		});
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



