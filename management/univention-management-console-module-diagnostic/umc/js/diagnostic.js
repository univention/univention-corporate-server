/*
 * Copyright 2014 Univention GmbH
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
	'dojo/_base/declare',
	'dojo/_base/lang',
	'dojo/_base/array',
	'dojo/promise/all',
	'dojo/on',
	"dojo/dom-class",
	"dojo/dom-construct",
	"dojo/Deferred",
	"dojox/html/styles",
	'umc/dialog',
	'umc/app',
	'umc/tools',
	'umc/widgets/Page',
	'umc/widgets/Module',
	'umc/widgets/TextBox',
	'umc/widgets/ComboBox',
	'umc/widgets/ContainerWidget',
	'umc/widgets/TitlePane',
	"umc/widgets/GalleryPane",
	"dojo/data/ObjectStore",
	"dojo/store/Memory",
	"dojo/store/Observable",
	"umc/widgets/ProgressBar",
	"umc/widgets/Button",
	"umc/widgets/Text",
	"put-selector/put",
	'umc/modules/diagnostic/DetailPage',
	'umc/i18n!umc/modules/diagnostic'
], function(declare, lang, array, all, on, domClass, domConstruct, Deferred, styles, dialog, app, tools, Page, Module, TextBox, ComboBox, ContainerWidget, TitlePane, GalleryPane, ObjectStore, Memory, Observable, ProgressBar, Button, Text, put, DetailPage, _) {

	styles.insertCssRule('.diagnosticDescription', '/*background-color: #e6e6e6; border: thin solid #d3d3d3;*/ white-space: pre; word-break: break-all; word-wrap: break-word;');
	styles.insertCssRule('.diagnosticGrid h1', 'margin-bottom: 0; border-bottom: thin solid #000');
	styles.insertCssRule('.diagnosticGrid .dijitButtonText', 'font-size: 1em');
	styles.insertCssRule('.diagnosticGrid span.critical', 'color: red;');
	styles.insertCssRule('.diagnosticGrid span.warning', 'color: orange;');

	GalleryPane = declare([GalleryPane], {

		getItemName: function(item) {
			return item.title;
		},

		getButtonCallback: function(button, item) {
			return lang.hitch(this, function() {
				this.module._runDiagnose(item, {action: button.action});
			});
		},

		renderRow: function(item) {
			var div = put('div.diagnosticGrid');
			var heading = put(div, 'h1');
			if (item.type) {
				put(heading, lang.replace('span.{type}', item), lang.replace('{type}: ', item));
			}
			put(heading, 'span', item.title);

			var description = item.description;
			array.forEach(item.umc_modules, function(link) {
				var repl = link[1] ? ('{' + link[0] + ':' + link[1] + '}') : ('{' + link[0] + '}');
				link = app.linkToModule(link[0], link[1]);
				if (link) {
					if (description.indexOf(repl) !== -1) {
						description = description.replace(repl, link);
					} else {
						domConstruct.create('div', {innerHTML: link}, div);
					}
				}
			});
			new Text({content: description}).placeAt(put(div, 'div.diagnosticDescription'));

			array.forEach(item.links, function(link) {
				domConstruct.create('a', {href: link[0], innerHTML: link[1] || link[0]}, div);
			});

			var buttons = put(div, 'div');
			array.forEach(item.buttons, lang.hitch(this, function(button) {
				new Button({
					label: button.label,
					callback: this.getButtonCallback(button, item)
				}).placeAt(buttons);
			}));

			return div;
		}
	});

	return declare('umc.modules.diagnostic',  Module, {

		_grid: null,
		_overviewPage: null,
		_detailPage: null,
		idProperty: 'plugin',
		standbyOpacity: 0.5,

		postMixInProperties: function() {
			this.inherited(arguments);
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._overviewPage = new Page({
				headerText: this.description,
				helpText: _('Within this module the system can be anaylzed for various known problems. ') +
				_('If the system is able to automatically repair found problems it offers the function in the context menu. ') +
				_('Otherwise the problems can be solved manually with help of the displayed links to articles by using the linked UMC modules. ')
			});
			this.addChild(this._overviewPage);

//			this._runButton = new Button({
//				label: _('Start full diagnose'),
//				callback: lang.hitch(this, '_runFullDiagnose'),
//				region: 'nav'
//			});

			this._grid = new GalleryPane({
				store: this._store,
				query: function(item) {
					return item.success === false;
				},
				region: 'main'
			});

//			this._overviewPage.addChild(this._runButton);
//			this._overviewPage.addChild(this._progressBar);
			this._overviewPage.addChild(this._grid);
			this.container = new ContainerWidget({});
			this._overviewPage.addChild(this.container);
			this._overviewPage.startup();

			this.load().then(lang.hitch(this, function() {
				this._runFullDiagnose().then(lang.hitch(this, 'renderGrid'));
			}));
		},

		load: function() {
			return this.standbyDuring(this.umcpCommand('diagnostic/query')).then(lang.hitch(this, function(response) {
				this._store = new Observable(new Memory({
					idProperty: 'plugin',
					data: response.result
				}));
				this._grid.set('store', this._store);
			}));
		},

		renderGrid: function() {
			return;
			this._grid.store.query(this._grid.query).forEach(lang.hitch(this, function(item) {
				this.container.addChild(new TitlePane({
					title: item.title,
					content: GalleryPane.renderRow(item)
				}));
				
			}));
		},

		_runFullDiagnose: function() {
			var plugins = this._grid.store.query();
			this._stepInc = 100 / plugins.length;

			this._progressBar = new ProgressBar({});
			this._progressBar.setInfo(_('Running full diagnose...'), undefined, Infinity);

			var deferred = new Deferred();
			this._progressBar.feedFromDeferred(deferred);

			return this.standbyDuring(all(array.map(plugins, lang.hitch(this, function(plugin) {

				this._grid.store.put(lang.mixin(plugin, {
					'status': 'loading'
				}));
				this._grid.set('query', this._grid.query);

				return this._runDiagnose(plugin).then(lang.hitch(this, function() {
					var percentage = this._progressBar._progressBar.get('value') + this._stepInc;
					deferred.progress({
						message: _('Diagnose of "%s" was successful', plugin.title),
						percentage: percentage
					});
				}));
			}))), this._progressBar).then(lang.hitch(this, function() {
//				this.load();
			}));
		},

		_runSingleDiagnose: function(plugin, opts) {
			this.standbyDuring(this._runDiagnose(plugin, opts));
		},

		_runDiagnose: function(plugin, opts) {
			var run = this.umcpCommand('diagnostic/run', lang.mixin({plugin: plugin.id}, opts));
			run.then(lang.hitch(this, function(data) {
				this._grid.store.put(lang.mixin(plugin, data.result, {
					'status': 'executed'
				}));

				this._grid.set('query', this._grid.query);
			}));
			return run;
		}

	});
});
