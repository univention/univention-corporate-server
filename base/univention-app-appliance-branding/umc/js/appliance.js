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
/*global define*/

define([
	"dojo/when",
	"dojo/dom-class",
	"dojo/_base/lang",
	"umc/store",
	"dojo/topic",
	"put-selector/put",
	"umc/app",
	"umc/tools",
	"umc/widgets/TitlePane",
	"umc/widgets/LabelPane",
	"umc/widgets/Text",
	"umc/widgets/CheckBox",
	"umc/i18n!umc/modules/appliance"
], function(when, domClass, lang, store, topic, put, app, tools, TitlePane, LabelPane, Text, CheckBox, _) {

	var ucrStore = store('key', 'ucr');
	var detailsPane = null;
	var notShowAgainCheckBox = null;
	var loadFirstSteps = function(){
		tools.umcpCommand('appcenter/get', {'application': 'owncloud82'}).then( function(data) {
			var loadedApp = data.result
			if (loadedApp === null) {
				console.warn('Error: Empty response');
			}
			notShowAgainCheckBox = new CheckBox({
				name: 'close_first_steps',
				value: false,
				checked: false,
				onChange: function() {notShowAgainChange()}
			});
			var notShowAgainLabel = new LabelPane({
				content: notShowAgainCheckBox,
				label: _('Do not show again.'),
			})
			var readme = new Text({
				content: loadedApp.readme
			});
			detailsPane = new TitlePane({
				title: _("First Steps"),
				open: false
			});
			detailsPane.addChild(readme);
			detailsPane.addChild(notShowAgainLabel);

			// app.js uses its subscription to /dojo/hashchange to show the right category
			// after a page reload. But this script is loaded after that event trigert.
			// So we have to manually check if we should show the first steps after
			// a page reload
			var hideFirstSteps = window.location.hash !== "#category=_appliance_";
			domClass.toggle(detailsPane.domNode, 'dijitHidden', hideFirstSteps);
			toggleDetailsPane().then(put(app._grid.domNode, '-', detailsPane.domNode));
		});
	};

	var firstStepsToggleSubscription = function(){
		topic.subscribe('/dojo/hashchange', function(_hash) {
			// /dojo/hashchange publishes category and module changes
			var hash = decodeURIComponent(_hash);
			if (hash.length > 7 && hash.substr(0,8) === 'category') {
				var hideFirstSteps = hash !== 'category=_appliance_';
				domClass.toggle(detailsPane.domNode, 'dijitHidden', hideFirstSteps);
			};
		});
	};

	var toggleDetailsPane = function(){
		// ucrStore.get doesn't like empty ucr variables
		return tools.ucr('umc/web/appliance/close_first_steps').then(function(res){
			detailsPane.set('open', !tools.isTrue(res['umc/web/appliance/close_first_steps']));
		});
	};

	var notShowAgainChange = function(){
		ucrStore.add({
			key: 'umc/web/appliance/close_first_steps',
			value: notShowAgainCheckBox.get('checked').toString()
		}).then(function(){
			toggleDetailsPane();
		});
	};

	//app.registerOnStartup(function() {
		loadFirstSteps();
		firstStepsToggleSubscription();
	//});

	return null;
});
