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

dojo.provide("umc.modules.roomadmin");

dojo.require("umc.widgets.TabbedModule");
dojo.require("umc.widgets.Module");
dojo.require( "umc.widgets.Form" );
dojo.require( "umc.widgets.Grid" );
dojo.require( "dojox.layout.TableContainer" );
dojo.require( "dijit.layout.BorderContainer" );

dojo.declare("umc.modules.roomadmin", umc.widgets.TabbedModule, {
	// summary:
	//		Module for modifying and displaying UCR variables on the system.

	_grid: null,
	_store: null,
	_searchWidget: null,
	_detailDialog: null,
	_contextVariable: null,

	buildRendering: function() {
		// call superclass' method
		this.inherited(arguments);
		this.addChild( this.overviewTab() );
		this.addChild( new umc.widgets.Page( {
			title: 'Präsentation',
			content: '&lt;Leer&gt;'
		}));
		this.addChild( new umc.widgets.Page( {
			title: 'Beobachtung',
			content: '&lt;Leer&gt;'
		}));
		//this.addTab( 'Übersicht', this.overviewTab() );
		//this.addTab( 'Präsentation', '&lt;Leer&gt;' );
		//this.addTab( 'Beobachtung', '&lt;Leer&gt;' );
	},

	overviewTab: function() {
		// define actions
		var actions = [{
			name: 'logout',
			label: 'Abmelden',
			description: 'Den aktuell angemeldeten Benutzer abmelden',
			iconClass: 'dijitIconAdd',
			isStandardAction: true,
			isContextAction: true,
			callback: dojo.hitch(this, function(selection) {
				// get all users
				var users = [];
				dojo.forEach(selection, function(i) {
					users.push(i.user);
				});
				var usersStr = users.join(', ');

				// logout users after confirmation
				umc.app.confirm('Sind Sie sicher, dass Sie die folgenden Benutzer abmelden möchten: ' + usersStr + ' ?', [{
					label: 'Abbmelden',
					'default': true,
					callback: function() {
						console.log('# callback abmelden');
						umc.app.notify('Die folgenden Benutzer wurden vom System abgemeldet: ' + usersStr);
					}
				}, {
					label: 'Abbrechen'
				}]);
			})
		},{
			name: 'poweroff',
			label: 'Ausschalten',
			description: 'Den Rechner ausschalten',
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isContextAction: true,
			callback: dojo.hitch(this, function(selection) {
				// get all users
				var computers = [];
				dojo.forEach(selection, function(i) {
					computers.push(i.computer);
				});
				var computersStr = computers.join(', ');

				// logout users after confirmation
				umc.app.confirm('Sind Sie sicher, dass Sie die folgenden Rechner ausschalten möchten: ' + computersStr + ' ?', [{
					label: 'Ausschalten',
					'default': true,
					callback: function() {
						umc.app.notify('Die folgenden Rechner wurden abgeschaltet: ' + computersStr);
					}
				}, {
					label: 'Abbrechen'
				}]);
			})
		}];
		// define grid columns
		var columns = [{
			name: 'computer',
			label: 'Rechner',
			description: 'Name des Rechners',
			editable: false,
			iconField: 'computericon'
		}, {
			name: 'user',
			label: 'Benutzer',
			description: 'der aktuell angemeldete Benutzer',
			editable: false
		},{
			name: 'internet',
			label: 'Internet',
			description: 'Zeigt an, ob der Internetzugriff aktiviert ist',
			editable: true,
			type: 'checkbox',
			callback: function(values) {
				if (values.internet) {
					umc.app.confirm('Sind Sie sicher, dass Sie den Internetzugriff aktivieren möchten?', [{
						label: 'Aktivieren',
						'default': true,
						callback: function() {
							umc.app.notify('Internetzugriff wurde aktiviert auf dem Rechner: ' + values.computer);
						}
					}, {
						label: 'Abbrechen'
					}]);
				}
				else {
					umc.app.confirm('Sind Sie sicher, dass Sie den Internetzugriff deaktivieren möchten?', [{
						label: 'Deaktivieren',
						'default': true,
						callback: function() {
							umc.app.notify('Internetzugriff wurde deaktiviert auf dem Rechner: ' + values.computer);
						}
					}, {
						label: 'Abbrechen'
					}]);
				}
			}
		},{
			name: 'locked',
			label: 'Gesperrt',
			description: 'Zeigt an, ob der Rechner für den Benutzer gesperrt ist',
			editable: true,
			type: 'checkbox'
		}];

		// generate the data grid
		this._grid = new umc.widgets.Grid({
			region: 'center',
			actions: actions,
			columns: columns,
			idField: 'computer',
			umcpSearchCommand: 'roomadmin/search',
			umcpSetCommand: 'roomadmin/set'
		});

		//
		// add search widget
		//

		// define the different search widgets
		var widgets = [{
			type: 'ComboBox',
			name: 'room',
			value: 'all',
			description: 'Auswahl des gewünschten Raumes',
			label: 'Raum',
			staticValues: {
				all: 'Alle'
			},
			umcpValues: 'roomadmin/rooms'
		},{
			type: 'TextBox',
			name: 'computer',
			value: '*',
			description: 'Sucht den Begriff im Rechnernamen',
			label: 'Rechner'
		},{
			type: 'TextBox',
			name: 'user',
			value: '*',
			description: 'Sucht den Begriff im Benutzernamen',
			label: 'Benutzername'
		}];

		// define all buttons
		var buttons = [{
			name: 'submit',
			label: 'Suchen',
			callback: dojo.hitch(this._grid, 'umcpSearch')
		}, {
			name: 'reset',
			label: 'Zurücksetzen'
		}];

		// define the search form layout
		var layout = [
			[ 'room', '' ],
			[ 'computer', 'user' ]
		];

		// generate the search widget
		this._searchWidget = new umc.widgets.Form({
			region: 'top',
			widgets: widgets,
			buttons: buttons,
			layout: layout
		});
		
		// simple handler to enable/disable standby mode
		dojo.connect(this._grid, 'umcpSearch', this, function() {
			this.standby(true);
		});
		dojo.connect(this._grid, 'onUmcpSearchDone', this, function() {
			this.standby(false);
		});

		// put everything together
		var page = new umc.widgets.Page({
			title: 'Übersicht',
			description: 'Dies Übersicht zeigt Details zu dem ausgewählten Computerraum und bietet die Möglichkeit, Einfluss auf den Internetzugriff und dem Zugang zum Rechner ansich zu nehmen. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus vehicula purus eu ipsum tempus quis vestibulum nunc aliquet. Donec sapien nunc, tempor sit amet malesuada vitae, cursus quis urna.',
			tooltip: 'Rechner eines Raumes kontrollieren'
		});
		page.addChild( this._searchWidget );
		page.addChild( this._grid ) ;

		return page;
	}

});


