/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.modules._udm.CreateReportDialog");

dojo.require("dojo.DeferredList");
dojo.require("umc.i18n");
dojo.require("umc.widgets.ContainerWidget");
dojo.require("umc.widgets.Form");
dojo.require("umc.widgets.StandbyMixin");
dojo.require("umc.tools");
dojo.require("umc.widgets.Text");
dojo.require("umc.widgets.Button");

dojo.declare("umc.modules._udm.CreateReportDialog", [ dijit.Dialog, umc.widgets.StandbyMixin, umc.i18n.Mixin ], {
	// summary:
	//		Dialog class for creating Univention Directory Reports.

	// use i18n information from umc.modules.udm
	i18nClass: 'umc.modules.udm',

	// umcpCommand: Function
	//		Reference to the module specific umcpCommand function.
	ucmpCommand: null,

	// moduleFlavor: String
	//		Specifies the flavor of the module. This property is necessary to decide what
	//		kind of dialog is presented: in the context of a particular UDM module or
	//		the UDM navigation.
	moduleFlavor: '',

	// LDAP DNs to include in the report
	objects: null,

	// list of available reports
	reports: null,

	// UDM object type name in singular and plural
	objectNameSingular: '',
	objectNamePlural: '',

	// internal reference to the dialog's form
	_form: null,

	_container: null,

	'class' : 'umcPopup',

	// force max-width
	style: 'max-width: 400px;',

	postMixInProperties: function() {
		this.inherited(arguments);

		// mixin the dialog title
		dojo.mixin(this, {
			title: this._( 'Report for %s', this.objectNameSingular )
		} );
	},

	buildRendering: function() {
		this.inherited(arguments);

		var reports = dojo.map( this.reports, function( item ) {
			return { id : item, label: item }; } );

		var widgets = [ {
			type: 'ComboBox',
			name: 'report',
			label: this._( 'Report' ),
			description: this._( 'The report template that should be used for the report.' ),
			value: this.reports[ 0 ],
			staticValues: reports
		} ];
		var layout = [ 'report' ];

		// buttons
		var buttons = [ {
			name: 'create',
			label: this._( 'Create' ),
			'default': true,
			callback: dojo.hitch( this, function() {
				this.onDone( this._form.gatherFormValues() );
			} )
		}, {
			name: 'cancel',
			label: this._( 'Cancel' ),
			callback: dojo.hitch( this, function() {
				this.destroyRecursive();
			} )
		} ];

		// now create a Form
		this._form = new umc.widgets.Form( {
			widgets: widgets,
			layout: layout,
			buttons: buttons
		} );
		this._container = new umc.widgets.ContainerWidget( {} );
		this._container.addChild( this._form );
		this.set( 'content', this._container );
	},

	onDone: function( options ) {
		this.standby( true );

		this._container.removeChild( this._form );
		var waiting = new umc.widgets.Text( {
			content: this._( '<p>Generating %s report for %d objects.</p><p>This may take a while</p>', this.objectNameSingular, this.objects.length )
		} );
		this._container.addChild( waiting );
		this.set( 'title', this._( 'Creating the report ...' ) );
		this.umcpCommand( 'udm/reports/create', { objects: this.objects, report: options.report } ).then( dojo.hitch( this, function( data ) {
			var title = '';
			var message = '';

			this.standby( false );
			this._container.removeChild( waiting );
			if ( true === data.result.success ) {
				message = dojo.replace( '<p>{0}</p>', [ this._( 'The %s can be downloaded at<br><br><a target="_blank" href="%s">%s report</a>', data.result.docType, data.result.URL, this.objectNameSingular ) ] );
				title = this._( 'Report has been created' );
			} else {
				title = this._( 'Report creation has failed' );
				message = this._( 'For some reason the report could not be created. Details for the problems can be found in the log files.' );
			}
			this.set( 'title', title );
			this._container.addChild( new umc.widgets.Text( { content: message } ) );
			var btnContainer = new umc.widgets.ContainerWidget( {
				style: 'text-align: center;',
				'class' : 'umcButtonRow'
			} );
			btnContainer.addChild( new umc.widgets.Button( {
				defaultButton: true,
				label: this._( 'Close' ),
				style: 'margin-left: auto;',
				callback: dojo.hitch( this, function() {
					this.destroyRecursive();
				} )
			} ) );
			this._container.addChild( btnContainer );
		} ) );
	}
});




