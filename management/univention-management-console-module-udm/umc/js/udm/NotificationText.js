/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2012-2022 Univention GmbH
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

define([
	"dojo/_base/declare",
	"dojo/_base/lang",
	"dojo/dom-class",
	"dojo/on",
	"umc/widgets/Text",
], function(declare, lang, domClass, on, Text) {
	return declare("umc.modules.udm.NotificationText", [Text], {
		// summary:
		//		This class extends the normal Text widget in order to encapsulate
		//		some UDM specific notification behavior.

		buildRendering: function() {
			this.inherited(arguments);
			domClass.add(this.domNode, 'udmNewObjectDialog__successNotification');
			this.set('visible', false);
			on(this.domNode, 'click', lang.hitch(this, '_hideMessage'));
		},

		showSuccess: function(message) {
			this.set('visible', true);
			this.set('content', message);
		},

		_hideMessage: function(stopDeferred) {
			this.set('visible', false);
		},
	});
});
