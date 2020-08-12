/*
 * Copyright 2020 Univention GmbH
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
/*global define*/

/**
 * @module portal/PortalMenu
 */
define([
	"dojo/_base/declare",
	"dojo/dom-class",
	"dojo/on",
	"dijit/form/Button",
	"umc/menu/Menu",
	"umc/tools",
	"umc/menu",
	"put-selector/put",
	"./portalContent",
	"umc/i18n!portal"
], function(
	declare, domClass, on, Button, Menu, tools, menu, put, portalContent, _
) {
	return declare("PortalMenu", [Menu], {
		constructor: function() {
			this._addeduserLinkIds = [];
			this._addedmiscLinkIds = [];
		},

		addEnterEditModeButton: function() {
			var editButton = new Button({
				'class': 'editModeButton ucsTextButton',
				iconClass: 'iconEdit',
				label: _('Edit Portal'),
				onClick: () => {
					this.onEnterEditMode();
				}
			});
			put(this.domNode, editButton.domNode);
			editButton.startup();
		},

		onEnterEditMode: function() {
		},

		_addeduserLinkIds: null,
		_addedmiscLinkIds: null,
		addLinks: function() {
			const linkCats = portalContent.links();

			for (const cat in linkCats) {
				const links = linkCats[cat];
				const basePrio = cat === 'user' ? 150 : -150;
				const addedIds = this[`_added${cat}LinkIds`];
				if (links.length && !addedIds.length) {
					menu.addSeparator({
						priority: basePrio
					});
				}

				for (const link of links) {
					if (!addedIds.includes(link.dn)) {
						addedIds.push(link.dn);
						var linkPrio = basePrio;
						if (link.priority) {
							linkPrio += link.priority;
						}
						menu.addEntry({
							onClick: function() {
								switch (link.linkTarget) {
									case 'samewindow':
										window.location = link.web_interface;
										break;
									case 'newwindow':
										window.open(link.web_interface);
										break;
									case 'embedded':
										topic.publish('/portal/iframes/open', link.dn, link.name, link.logo, link.href);
										break;
								}
							},
							label: link.name,
							priority: basePrio + linkPrio
						});
					}
				}
			}
		},
	});
});




