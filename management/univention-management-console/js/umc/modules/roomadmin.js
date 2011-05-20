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
			content: '<Leer>'
		}));
		this.addChild( new umc.widgets.Page( {
			title: 'Beobachtung',
			content: '<Leer>'
		}));
		//this.addTab( 'Übersicht', this.overviewTab() );
		//this.addTab( 'Präsentation', '<Leer>' );
		//this.addTab( 'Beobachtung', '<Leer>' );
	},

	overviewTab: function() {
		// define actions
		var actions = [{
			name: 'logout',
			label: 'Abmelden',
			description: 'Den aktuell angemeldeten Benutzer abmelden',
			iconClass: 'dijitIconAdd',
			isStandardAction: true,
			isContextAction: true
		},{
			name: 'poweroff',
			label: 'Ausschalten',
			description: 'Den Rechner ausschalten',
			iconClass: 'dijitIconEdit',
			isStandardAction: true,
			isContextAction: true
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
					umc.app.notify('Internetzugriff wurde aktiviert auf dem Rechner: ' + values.computer);
				}
				else {
					umc.app.notify('Internetzugriff wurde deaktiviert auf dem Rechner: ' + values.computer);
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
			label: 'Name',
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
			description: 'Hier können Gruppen für Arbeitskreise oder Projekte angelegt, bearbeitet oder gelöscht werden. Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vivamus vehicula purus eu ipsum tempus quis vestibulum nunc aliquet. Donec sapien nunc, tempor sit amet malesuada vitae, cursus quis urna. Aenean molestie tempus faucibus. Donec at varius nisl. Pellentesque lobortis suscipit ante at dictum. Nulla sed mauris eget dolor pellentesque egestas at a nisl. Nam mollis urna in ipsum placerat vitae sagittis purus tristique.',
			tooltip: 'Rechner eines Raumes kontrollieren'
		});
		page.addChild( this._searchWidget );
		page.addChild( this._grid ) ;

		return page;
	}

});


