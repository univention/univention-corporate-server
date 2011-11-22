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

dojo.provide("umc.widgets._ModuleMixin");

dojo.require("umc.store");
dojo.require("umc.tools");

dojo.declare("umc.widgets._ModuleMixin", null, {
	// summary:
	//		Mixin class for all module classes. It adds some module specific
	//		properties/methods.

	// idProperty: String
	//		Indicates the property to use as the identity property.
	//		The values of this property need to be unique.
	idProperty: '',

	// moduleFlavor: String
	//		Specifies the module flavor which may need to be communicated to
	//		the server via `umc.tool.umcpCommand()`.
	//		(Is specified automatically.)
	moduleFlavor: null,

	// moduleID: String
	//		ID of the module.
	//		(Is specified automatically.)
	moduleID: '',

	// moduleStore: umc.store.UmcpModuleStore
	//		A dojo object store interface for query/get/put/remove methods for the UMC
	//		module. Requests for operations on module items should be executed through
	//		this store interface. In this way, changes will be immediatly reflected to
	//		other parts of the GUI.
	//		(Is specified automatically.)
	moduleStore: null,

	// title: String
	//		Title of the page. This option is necessary for tab pages.
	//		(Is specified automatically.)
	title: '',

	postMixInProperties: function() {
		this.inherited(arguments);

		if (this.idProperty) {
			this.moduleStore = umc.store.getModuleStore(this.idProperty, this.moduleID, this.moduleFlavor);
		}
	},

	umcpCommand: function( /*String*/ commandStr, /*Object?*/ dataObj, /*Boolean?*/ handleErrors, /*String?*/ flavor, /*Object?*/ longPollingOptions ) {
		return umc.tools.umcpCommand( commandStr, dataObj, handleErrors, flavor || this.moduleFlavor, longPollingOptions );
	}
});


