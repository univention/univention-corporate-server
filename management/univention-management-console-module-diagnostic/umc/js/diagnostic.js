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
	'umc/tools',
	'umc/render',
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
	"dgrid/Selection",
	'umc/i18n!umc/modules/diagnostic'
], function(declare, lang, array, all, on, domClass, domConstruct, Deferred, styles, dialog, tools, render, Page, Module, TextBox, ComboBox, ContainerWidget, TitlePane, GalleryPane, ObjectStore, Memory, Observable, ProgressBar, Button, Text, put, Selection, _) {

	styles.insertCssRule('.diagnosticDescription', '/*background-color: #e6e6e6; border: thin solid #d3d3d3;*/ white-space: pre; word-break: break-all; word-wrap: break-word;');
	styles.insertCssRule('.diagnosticGrid h1', 'margin-bottom: 0; border-bottom: thin solid #000');
	styles.insertCssRule('.diagnosticGrid .dijitButtonText', 'font-size: 1em');
	styles.insertCssRule('.diagnosticGrid .critical span.dijitTitlePaneTextNode::before', lang.replace('color: red; content: "{0}";', [_('Critical: ')]));
	styles.insertCssRule('.diagnosticGrid .conflict span.dijitTitlePaneTextNode::before', lang.replace('color: darkorange; content: "{0}";', [_('Conflict: ')]));
	styles.insertCssRule('.diagnosticGrid .warning  span.dijitTitlePaneTextNode::before', lang.replace('color: orange; content: "{0}";', [_('Warning: ')]));
	styles.insertCssRule('.diagnosticGrid .problemfixed span.dijitTitlePaneTextNode::before', lang.replace('color: green; content: "{0}";', [_('Problem repaired: ')]));
	styles.insertCssRule('.diagnosticGrid .success span.dijitTitlePaneTextNode::before', lang.replace('color: green; content: "{0}";', [_('Success: ')]));
	styles.insertCssRule('.diagnosticGrid .problem span.dijitTitlePaneTextNode::before', lang.replace('color: orange; content: "{0}";', [_('Problem: ')]));

	GalleryPane = declare([GalleryPane, Selection], {
		allowTextSelection: true
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
				_('Otherwise the problems can be solved manually with help of the displayed links to articles by using the linked UMC modules. '),
				headerButtons: [{
					name: 'start_diagnose',
					label: _('Start full diagnose'),
					callback: lang.hitch(this, '_runFullDiagnose')
				}]
			});
			this.addChild(this._overviewPage);

			this._grid = new GalleryPane({
				'class': 'diagnosticGrid',
				store: this._store,
				renderRow: lang.hitch(this, function(item) {
					var row = this.renderRow(item);
					this.own(row);
					return row.domNode;
				}),
				query: function(item) {
					// only show failed entries
					return item.success === false;
				},
				sort: 'type', // FIXME: sort by group, 1. Critical 2. Conflict 3. Warning
				noDataMessage: _('No problems could be detected.'),
				loadingMessage: _('Analyzing for problems...'),
				region: 'main'
			});
			this._overviewPage.addChild(this._grid);

			this._overviewPage.startup();

			this.load().then(lang.hitch(this, function() {
				this._runFullDiagnose();
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

		renderRow: function(item) {
			var div = put('div');

			var description = item.description;
			array.forEach(item.umc_modules, function(module) {
				var repl = module.flavor ? ('{' + module.module + ':' + module.flavor + '}') : ('{' + module.module + '}');
				var link = tools.linkToModule(module);
				if (description.indexOf(repl) !== -1) {
					if (!link) {
						link = _('"%s - %s" Module (as Administrator)', module.module, module.flavor);
					}
					description = description.replace(repl, link);
				} else if (link) {
					domConstruct.create('div', {innerHTML: link}, div);
				}
			});

			array.forEach(item.links, function(link) {
				var a = domConstruct.create('a', {href: link.href, innerHTML: link.label || link.href});
				var repl = '{' + link.name  + '}';
				if (description.indexOf(repl) !== -1) {
					var content = domConstruct.create('div');
					content.appendChild(a);
					description = description.replace(repl, content.innerHTML);
				} else {
					div.appendChild(a);
				}
			});

			new Text({content: description}).placeAt(put(div, 'div.diagnosticDescription'));

			var buttons = render.buttons(array.map(item.buttons, lang.hitch(this, function(button) {
				return lang.mixin(button, {
					callback: this.getButtonCallback(button, item)
				});
			})), this);

			var buttonctn = put(div, 'div');
			array.forEach(buttons.$order$, function(button) {
				button.placeAt(buttonctn);
			});

			return new TitlePane({
				title: item.title,
				'class': '' + item.type,
				open: item.status == 'reloading',
				content: div
			});
		},

		getButtonCallback: function(button, item) {
			return lang.hitch(this, function() {
				this._runSingleDiagnose(item, {args: {action: button.action}});
			});
		},

		_runFullDiagnose: function() {
			var plugins = this._grid.store.query();
			this._stepInc = 100 / plugins.length;

			this._progressBar = new ProgressBar({
				region: 'nav'
			});
			this._progressBar.setInfo(_('Running full diagnose...'), undefined, Infinity);

			var deferred = new Deferred();
			this._progressBar.feedFromDeferred(deferred);

			return this.standbyDuring(all(array.map(plugins, lang.hitch(this, function(plugin) {
				return this._runDiagnose(plugin).then(lang.hitch(this, function() {
					var percentage = this._progressBar._progressBar.get('value') + this._stepInc;
					deferred.progress({
						message: _('Diagnose of "%s" was successful', plugin.title),
						percentage: percentage
					});
				}));
			}))), this._progressBar).then(lang.hitch(this, function() {
				if (!this._store.query(this._grid.query).length) {
					this._store.add({
						plugin: '_success_',
						success: false,
						type: 'success',
						title: _('No problems could be detected.'),
						description: ''
					});
					this._grid.set('query', this._grid.query);
				}
			}));
		},

// don't block with progressbar?
//		standby: function(standby, progressbar) {
//			if (this._progressBar) {
//				domClass.toggle(this._progressBar, 'dijitHidden', !standby);
//				if (!standby) {
//					this._overviewPage.removeChild(this._progressBar);
//					this._progressBar = null;
//				} else {
//					this._overviewPage.addChild(this._progressBar/*, 0*/);
//				}
//				return;
//			}
//			this.inherited(arguments, [standby]);
//		},

		_runSingleDiagnose: function(plugin, opts) {
			this._grid.store.put(lang.mixin(plugin, {
				'status': 'reloading'
			}));
			this._grid.set('query', this._grid.query);
			this.standbyDuring(this._runDiagnose(plugin, opts)).then(lang.hitch(this, function() {
				this.addNotification(_('Finished running diagnose of "%s" again.', plugin.title));
			}));
		},

		_runDiagnose: function(plugin, opts) {
			var run = this.umcpCommand('diagnostic/run', lang.mixin({plugin: plugin.id}, opts));
			run.then(lang.hitch(this, function(data) {
				this._grid.store.put(lang.mixin(plugin, data.result));

				this._grid.set('query', this._grid.query);
			}));
			return run;
		}

	});
});
