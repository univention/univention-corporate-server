/*
 * Copyright 2011-2012 Univention GmbH
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
/*global define console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/topic",
	"dijit/form/Button",
	"umc/tools",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_SelectMixin"
], function(declare, lang, array, on, topic, Button, tools, ContainerWidget, _SelectMixin) {
	return declare("umc.widgets.LinkList", [ ContainerWidget, _SelectMixin ], {
		// summary:
		//		Provides a list of buttons opening a given object

		name: '',

		value: null,

		disabled: false,

		// the widget's class name as CSS class
		'class': 'umcLinkList',

		onDynamicValuesLoaded: function() {
			this.store.fetch( {
				onComplete: lang.hitch( this, function ( items ) {
					array.forEach( items, lang.hitch( this, function( item ) {
						var btn = Button( {
							name : 'close',
							label : item.label,
							iconClass: tools.getIconClass( item.icon, 16 )
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
						on( btn, "click", moduleProps, function () {
							topic.publish( "/umc/modules/open", [ moduleProps.module, moduleProps.flavor, moduleProps ] );
						} );
						this.addChild( btn );
					} ) );
				} )
			} );
		},

		isValid: function() {
			return true;
		}
	});
});

