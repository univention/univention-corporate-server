/*
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */
/*global define,console*/

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/on",
	"dojo/topic",
	"umc/widgets/Button",
	"umc/tools",
	"umc/app",
	"umc/widgets/ContainerWidget",
	"umc/widgets/_SelectMixin"
], function(declare, lang, array, on, topic, Button, tools, app, ContainerWidget, _SelectMixin) {
	return declare([ ContainerWidget, _SelectMixin ], {
		// summary:
		//		Provides a list of buttons opening a given object

		name: '',

		value: null,

		disabled: false,

		// the widget's class name as CSS class
		baseClass: 'umcLinkList',

		postCreate: function() {
			this.inherited(arguments);

			this.on('valuesLoaded', lang.hitch(this, function(items) {
				array.forEach( items, lang.hitch( this, function( item ) {
					//  make sure that the item has all necessary properties
					if (!array.every(['module', 'id', 'objectType'], function(ikey) {
						if (!(ikey in item)) {
							console.log( 'LinkList: attribute module is missing');
							return false;
						}
						return true;
					})) {
						// item has not all necessary properties -> stop here
						return false;
					}

					// perpare information to open the referenced UDM object
					var moduleProps = {
						flavor : item.flavor,
						module : item.module,
						openObject: {
							objectDN : item.id,
							objectType : item.objectType
						}
					};

					// create new button
					var btn = new Button( {
						name : 'close',
						label : item.label,
						iconClass: tools.getIconClass( item.icon, 20, null, "background-size: contain" ),
						callback: function() {
							// open referenced UDM object
							if (app.getModule(moduleProps.module, moduleProps.flavor)) {
								topic.publish("/umc/modules/open", moduleProps.module, moduleProps.flavor, moduleProps);
							} else if (app.getModule(moduleProps.module, 'navigation')) {  // udm module
								topic.publish("/umc/modules/open", moduleProps.module, 'navigation', moduleProps);
							} else {
								topic.publish("/umc/modules/open", moduleProps.module, moduleProps.flavor, moduleProps);
							}
						}
					} );

					this.addChild( btn );
				}));
			}));
		},

		isValid: function() {
			return true;
		}
	});
});
