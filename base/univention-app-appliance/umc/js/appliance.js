/*
 * Copyright 2011-2016 Univention GmbH
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
	"dojo/promise/all",
	"dojo/dom-class",
	"dojo/_base/lang",
	"umc/store",
	"dojo/topic",
	"dojo/hash",
	"dojo/io-query",
	"dojo/request",
	"put-selector/put",
	"umc/app",
	"umc/tools",
	"umc/widgets/TitlePane",
	"umc/widgets/LabelPane",
	"umc/widgets/Text",
	"umc/widgets/CheckBox",
	"umc/i18n!umc/modules/appliance",
	"xstyle/css!./appliance.css"
], function(when, all, domClass, lang, store, topic, hash, ioQuery, request, put, app, tools, TitlePane, LabelPane, Text, CheckBox, _) {

	var promiseUcrValues = tools.ucr(['umc/web/appliance/close_first_steps', 'umc/web/appliance/name']);
	var readmePath = dojo.moduleUrl("umc/modules/appliance")
	var promiseReadme = request(readmePath + _('appliance_first_steps.README'));
	var ucrStore = store('key', 'ucr');
	var firstSteps = null;
	var checkBoxShowContentOfFirstSteps = null;

	all({
		ucrValues: promiseUcrValues,
		readme: promiseReadme,
	}).then(function(result) {
		var isFirstStepsClosed = tools.isTrue(result.ucrValues['umc/web/appliance/close_first_steps']);
		var readmeHeader = _("Welcome to Univention Management Console (UMC), " + 
							"the administration interface for your appliance. " + 
							"UMC is provided by Univention Corporate Server, " + 
							"the platform on which %s is running on.", result.ucrValues['umc/web/appliance/name'])
		var readmeText = '<p>' + readmeHeader + '</p>' + result.readme;

		var readme = new Text({
			content: readmeText
		});

		firstSteps = new TitlePane({
			'class': 'firstSteps',
			title: _("First Steps"),
			open: !isFirstStepsClosed
		});
		firstSteps.addChild(readme);

		put(firstSteps.titleBarNode.firstElementChild, 'div.firstStepsIcon');

		
		checkBoxShowContentOfFirstSteps = new CheckBox({
			name: 'hide_first_steps',
			value: isFirstStepsClosed,
			checked: isFirstStepsClosed,
			onChange: saveStateOfFirstSteps
		});
		var labelHideContent = new LabelPane({
			content: checkBoxShowContentOfFirstSteps,
			label: _('Hide content next time.')
		});
		firstSteps.addChild(labelHideContent);

		put(app._grid.domNode, '-', firstSteps.domNode);

		subscripeVisibilityCheckOnHashChange(checkVisbilityOfFirstSteps);
		checkVisbilityOfFirstSteps(hash());
	});

	var checkVisbilityOfFirstSteps = function(_hash) {
		var isFirstStepsHidden = _hash.indexOf("category=_appliance_") === -1;
		domClass.toggle(firstSteps.domNode, 'dijitHidden', isFirstStepsHidden);
	};

	var subscripeVisibilityCheckOnHashChange = function(callback) {
		topic.subscribe('/dojo/hashchange', function(hash) {
			callback(hash);
		});
	};

	var saveStateOfFirstSteps = function() {
		ucrStore.add({
			key: 'umc/web/appliance/close_first_steps',
			value: checkBoxShowContentOfFirstSteps.get('checked').toString()
		});
	};

	return null;
});
