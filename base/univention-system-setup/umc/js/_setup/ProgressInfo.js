/*
 * Copyright 2011 Univention GmbH
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

dojo.provide("umc.modules._setup.ProgressInfo");

dojo.require("umc.i18n");
dojo.require("umc.render");
dojo.require("umc.tools");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("dijit.ProgressBar");

dojo.declare("umc.modules._setup.ProgressInfo", [ umc.widgets.ContainerWidget, umc.i18n.Mixin ], {
	// summary:
	//		This class provides a widget providing detailed progress information

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.setup',

	umcpCommand: umc.tools.umcpCommand,

	style: 'width: 400px',

	_component: null,
	_message : null,
	_progressBar: null,

	buildRendering: function() {
		this.inherited(arguments);

		this._component = new umc.widgets.Text( { content : '' , style : 'width: 100%' } );
		this.addChild( this._component );
		this._progressBar = new dijit.ProgressBar( { style : 'width: 100%' } );
		this.addChild( this._progressBar );
		this._message = new umc.widgets.Text( { content : '', style : 'width: 100%' } );
		this.addChild( this._message );

		this._progressBar.set( 'value', 0 );
		this._progressBar.set( 'maximum', 100 );

		this.reset();
		this.startup();
	},

	reset: function() {
		this._component.set( 'content', this._( 'Initialize the configuration process ...' ) );
		this._message.set( 'content', '' );
		this._progressBar.set( 'value', 0 );
	},

	setInfo: function( component, message, percentage ) {
		this._component.set( 'content', component );
		this._progressBar.set( 'value', percentage );
		// make sure that at least a not breakable space is printed
		// ... this avoids vertical jumping of widgets
		this._message.set( 'content', message || '&nbsp;' );
	}
});



