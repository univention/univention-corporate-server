/*
 * Copyright 2011-2014 Univention GmbH
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
/*global define */

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/_base/array",
	"dijit/layout/StackContainer",
	"dojox/html/entities",
	"umc/tools",
	"umc/widgets/_ModuleMixin",
	"umc/widgets/StandbyMixin"
], function(declare, lang, array, StackContainer, entities, tools, _ModuleMixin, StandbyMixin) {
	return declare("umc.widgets.Module", [ StackContainer, _ModuleMixin, StandbyMixin ], {
		// summary:
		//		Basis class for module classes.
		//		It extends dijit.layout.StackContainer and adds some module specific
		//		properties/methods.

		// initial title set for the module
		defaultTitle: null,

		postMixInProperties: function() {
			this.inherited(arguments);
			this.defaultTitle = this.title;
		},

		resetTitle: function() {
			this.set( 'title', this.defaultTitle );
		},

		_setTitleAttr: function(title) {
			// dont set html attribute title
			// (looks weird)
			this._set('title', title);
		},

		_setTitleDetailAttr: function(detail) {
			var title = this.defaultTitle;
			if (detail) {
				title += ': ' + entities.encode(detail);
			}
			this.set('title', title);
			this._set('titleDetail', detail);
		},

		startup: function() {
			this.inherited(arguments);

			// FIXME: Workaround for refreshing problems with datagrids when they are rendered
			//        on an inactive tab.

			// iterate over all widgets
			array.forEach(this.getDescendants(), function(iwidget) {
				if (tools.inheritsFrom(iwidget, 'dojox.grid._Grid')) {
					// hook to onShow event
					this.on('show', lang.hitch(this, function() {
						iwidget.startup();
					}));
				}
			}, this);
		}
	});
});

