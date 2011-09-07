/*global console MyError dojo dojox dijit umc */

dojo.provide("umc.widgets.LinkList");

dojo.require("dijit.form.Button");
dojo.require("umc.widgets.ContainerWidget");
dojo.provide("umc.widgets._SelectMixin");
dojo.require("umc.tools");
dojo.require("umc.render");

dojo.declare("umc.widgets.LinkList", [ umc.widgets.ContainerWidget, umc.widgets._SelectMixin, umc.i18n.Mixin ], {
	// summary:
	//		Provides a list of buttons opening a given object 

	name: '',

	value: null,

	disabled: false,

	i18nClass: 'umc.app',

	// the widget's class name as CSS class
	'class': 'umcLinkList',

	onDynamicValuesLoaded: function() {
		this.store.fetch( {
						  onComplete: dojo.hitch( this, function ( items ) {
							  dojo.forEach( items, dojo.hitch( this, function( item ) {
												var btn = umc.widgets.Button( {
																				 name : 'close',
																				 label : item.label,
																				 iconClass: umc.tools.getIconClass( item.icon, 16 )
																			 } );
												if ( ! this.store.hasAttribute( item, 'module' ) ) {
													console.log( 'LinkList: attribute module is missing');
													return;
												}
												if ( ! this.store.hasAttribute( item, 'id' ) ) {
													console.log( 'LinkList: attribute objectDN is missing');
													return;
												}
												if ( ! this.store.hasAttribute( item, 'objectType' ) ) {
													console.log( 'LinkList: attribute objectType is missing');
													return;
												}
												var moduleProps = {
													flavor : this.store.getValue( item, 'flavor', null ),
													module : this.store.getValue( item, 'module', null ),
													openObject: {
														objectDN : this.store.getValue( item, 'id', null ),
														objectType : this.store.getValue( item, 'objectType', null )
													}
												};
												this.store.getValue( item, 'objectType', null );
												dojo.connect( btn, "onClick", moduleProps, function () {
																  dojo.publish( "/umc/modules/open", [ moduleProps.module, moduleProps.flavor, moduleProps ] );
															  } );
												this.addChild( btn );
											} ) );
							  } ) } );
	},


	isValid: function() {
		return true;
	}

});


