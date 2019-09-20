/*
 * Copyright 2013-2019 Univention GmbH
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
/*global define,require,window,Piwik*/

define([
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/kernel",
	"dojo/topic",
	"dojo/store/Memory",
	"dojox/timing",
	"umc/store",
	"umc/tools"
], function(lang, array, kernel, topic, Memory, timing, store, tools) {
	var actionStore = new Memory({data: []});
	var storeId = 0;
	var maxStoreItems = 1000;
	var lastTimestamp = 0;
	var piwikSendTimer = new timing.Timer(500);
	var piwikTracker = null;

	var _buildSiteTitle = function(parts) {
		var titleStr = [];
		array.forEach(parts, function(i) {
			if (i) {
				// ignore values that are: null, undefined, ''
				i = i + ''; // force element to be string...
				titleStr.push(i.replace(/\//g, '-'));
			}
		});

		// join elements with '/' -> such that a hierarchy can be recongnized by Piwik
		return titleStr.join('/');
	};

	var actionDict = function(parts) {
		var timestamp = Math.floor((new Date()).getTime()/1000);
		if (lastTimestamp >= timestamp) {
			timestamp = lastTimestamp + 1;
		}
		lastTimestamp = timestamp;
		var loc = lang.mixin({}, window.location);
		loc.port = loc.port ? ':' + loc.port : '';
		var action =  {
			siteTitle: _buildSiteTitle(parts),
			url: lang.replace('{protocol}//{hostname}{port}{pathname}', loc),
			numOfTabs: tools.status('numOfTabs'),
			timestamp: timestamp
		};
		return action;
	};

	var sendOldestAction = function() {
		var storeItem = actionStore.query({}, {count: 1})[0];
		if (storeItem) {
			var actionData = storeItem.actionData;
			actionStore.remove(storeItem.id);
			piwikTracker.setDocumentTitle(actionData.siteTitle);
			piwikTracker.setCustomUrl(actionData.url);
			piwikTracker.setCustomVariable(1, 'numOfTabs', actionData.numOfTabs, 'page');
			piwikTracker.appendToTrackingUrl('cdt=' + actionData.timestamp);
			piwikTracker.trackPageView();
		}
		return;
	};

	var storeAction = function() {
		if (actionStore.query().length < maxStoreItems) {
			actionStore.put({id: storeId, actionData: actionDict(arguments)});
			storeId += 1;
		}
		return;
	};

	var loadPiwik = function() {
		//console.log('### loadPiwik');
		if (piwikTracker || tools.status('piwikDisabled')) {
			// piwik has already been loaded
			return;
		}

		require(["https://www.piwik.univention.de/piwik.js"], function() {
			// create a new tracker instance
			piwikTracker = Piwik.getTracker('https://www.piwik.univention.de/piwik.php', 14);
			piwikTracker.setCustomVariable(1, 'ucsVersion', tools.status('ucsVersion'), 'visit');
			piwikTracker.setCustomVariable(2, 'systemUUID', tools.status('uuid/system') || 'unknown', 'visit');
			piwikTracker.enableLinkTracking();
			piwikSendTimer.onTick = sendOldestAction;
			piwikSendTimer.start();
		});
	};

	loadPiwik();

	// subscribe to all topics containing interesting actions
	topic.subscribe('/umc/actions', storeAction);

	// subscribe to load piwik
	topic.subscribe('/umc/piwik/load', loadPiwik);

	// send initial action that page was loaded
	topic.publish('/umc/actions', 'page', 'loaded', kernel.locale);
});
