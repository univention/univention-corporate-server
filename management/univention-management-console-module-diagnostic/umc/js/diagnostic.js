/*
 * Copyright 2014-2019 Univention GmbH
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
	'dojo/_base/declare',
	'dojo/_base/lang',
	'dojo/_base/array',
	'dojo/promise/all',
	"dojo/dom-construct",
	"dojo/Deferred",
	"dojox/html/styles",
	"dijit/Destroyable",
	'umc/tools',
	'umc/render',
	'umc/widgets/Page',
	'umc/widgets/Module',
	'umc/widgets/ContainerWidget',
	'umc/widgets/TitlePane',
	"dojo/store/Memory",
	"dojo/store/Observable",
	"umc/widgets/ProgressBar",
	"umc/widgets/Text",
	"dgrid/Selection",
	"dgrid/List",
	"dgrid/extensions/DijitRegistry",
	'umc/i18n!umc/modules/diagnostic',
	"xstyle/css!./diagnostic.css"
], function(declare, lang, array, all, domConstruct, Deferred, styles, Destroyable, tools, render, Page, Module,
	ContainerWidget, TitlePane, Memory, Observable, ProgressBar, Text, Selection, List, DijitRegistry, _) {

	tools.forIn({
		critical: _('Critical: '),
		conflict: _('Conflict: '),
		warning:  _('Warning: '),
		problemfixed: _('Problem repaired: '),
		success: _('Success: '),
		problem: _('Problem: ')
	}, function(key, value) {
		styles.insertCssRule(lang.replace('.umc-diagnostic .diagnostic-{0} span.dijitTitlePaneTextNode::before', [key]), lang.replace('content: "{0}";', [value]));
	});

	var Grid = declare([List, DijitRegistry, Destroyable, Selection], {
		allowTextSelection: true,

		getButtonCallback: null,

		query: {},

		queryOptions: {},

		_setStore: function(value) {
			this.store = value;
			this._renderQuery();
		},

		_setQuery: function(value) {
			this.query = value;
			this._renderQuery();
		},

		_setQueryOptions: function(value) {
			this.queryOptions = value;
			this._renderQuery();
		},

		_renderQuery: function() {
			this.refresh();
			this.renderArray(this.store.query(this.query, this.queryOptions));
		},

		postCreate: function() {
			this.inherited(arguments);

			// TODO: this changes with Dojo 2.0
			this.domNode.setAttribute("widgetId", this.id);
		},

		renderRow: function(item) {
			var div = new ContainerWidget({});

			var text = new Text({
				'class': 'umc-diagnostic-description'
			});
			this.own(text);
			div.addChild(text);

			var description = item.description;
			array.forEach(item.umc_modules, function(module) {
				var repl = module.flavor ? ('{' + module.module + ':' + module.flavor + '}') : ('{' + module.module + '}');
				var link = tools.linkToModule(module);
				if (description.indexOf(repl) !== -1) {
					if (!link) {
						link = _('"%(module)s - %(flavor)s" Module (as Administrator)', {module: module.module, flavor: module.flavor});
					}
					description = description.replace(repl, link);
				} else if (link) {
					var a = new Text({innerHTML: link});
					div.addChild(a);
				}
			});

			array.forEach(item.links, lang.hitch(this, function(link) {
				var a = domConstruct.create('div');
				a.appendChild(domConstruct.create('a', {href: link.href, innerHTML: link.label || link.href, target: '_blank', rel: 'noopener noreferrer'}));
				a = new Text({innerHTML: a.innerHTML});
				this.own(a);
				var repl = '{' + link.name  + '}';
				if (description.indexOf(repl) !== -1) {
					description = description.replace(repl, a.innerHTML);
				} else {
					div.addChild(a);
				}
			}));

			text.set('content', description);

			var buttons = render.buttons(array.map(item.buttons, lang.hitch(this, function(button) {
				return lang.mixin(button, {
					callback: this.getButtonCallback(button, item)
				});
			})), this);

			var buttonctn = new ContainerWidget();
			div.addChild(buttonctn);
			this.own(buttonctn);
			array.forEach(buttons.$order$, function(button) {
				buttonctn.addChild(button);
			});

			var titlePane = new TitlePane({
				title: item.title,
				'class': 'diagnostic-' + item.type,
				open: item.status === 'reloading',
				toggleable: item.plugin !== '_success_',
				content: div
			});
			this.own(titlePane);
			return titlePane.domNode;
		}
	});

	return declare('umc.modules.diagnostic',  Module, {

		_grid: null,
		_overviewPage: null,
		_detailPage: null,
		idProperty: 'plugin',
		standbyOpacity: 0.75,

		postMixInProperties: function() {
			this.inherited(arguments);
			this._openProgressBars = [];
		},

		destroy: function() {
			this.inherited(arguments);
			array.forEach(this._openProgressBars, lang.hitch(this, function(deferred) {
				if (!deferred.isFulfilled()) {
					deferred.cancel();
				}
			}));
		},

		buildRendering: function() {
			this.inherited(arguments);

			this._overviewPage = new Page({
				helpText: _('Within this module the system can be analyzed for various known problems. ') +
				_('If the system is able to automatically repair found problems it offers the function as additional buttons. ') +
				_('Otherwise the problems can be solved manually with help of the displayed links to articles by using the linked UMC modules. '),
				headerButtons: [{
					name: 'start_diagnose',
					label: _('Run system diagnosis'),
					callback: lang.hitch(this, '_runFullDiagnose')
				}],
				fullWidth: true
			});
			this.addChild(this._overviewPage);

			this._grid = new Grid({
				'class': 'umc-diagnostic',
				store: this._store,
				getButtonCallback: lang.hitch(this, 'getButtonCallback'),
				query: function(item) {
					// only show failed entries
					return item.success === false;
				},
				queryOptions: {
					sort: lang.hitch(this, 'sort')
				},
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

		sort: function(a, b) {
			var priority = {
				critical: 10,
				conflict: 9,
				warning:  7,
				problemfixed: 11,
				success: 11,
				problem: 8
			};
			var atype = priority[a.type] || 0;
			var btype = priority[b.type] || 0;
			if (atype === btype) {
				return a.plugin.localeCompare(b.plugin);
			} else if (atype > btype) {
				return -1;
			} else {
				return 1;
			}
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

		getButtonCallback: function(button, item) {
			return lang.hitch(this, function() {
				this._runSingleDiagnose(item, {args: {action: button.action}});
			});
		},

		refreshGrid: function() {
			this._grid._renderQuery();
		},

		_runFullDiagnose: function() {
			var plugins = this._grid.store.query();
			this._stepInc = 100 / plugins.length;

			this._progressBar = new ProgressBar({
				region: 'nav'
			});
			this.own(this._progressBar);
			this._progressBar.setInfo(_('Running full diagnosis...'), undefined, Infinity);

			var deferred = new Deferred();
			this._progressBar.feedFromDeferred(deferred);

			return this.standbyDuring(all(array.map(plugins, lang.hitch(this, function(plugin) {
				if (!plugin.id) {
					return;  // this is the success message
				}
				return this._runDiagnose(plugin).then(lang.hitch(this, function() {
					var percentage = this._progressBar._progressBar.get('value') + this._stepInc;
					deferred.progress({
						message: _('Diagnosis of "%s" was successful', plugin.title),
						percentage: percentage
					});
				}));
			}))), this._progressBar).then(lang.hitch(this, 'fixNoDataMessage'));
		},

		_runSingleDiagnose: function(plugin, opts) {
			this._grid.store.put(lang.mixin(plugin, {
				'status': 'reloading'
			}));
			this.refreshGrid();
			this.standbyDuring(this._runDiagnose(plugin, opts)).then(lang.hitch(this, function() {
				//this.addNotification(_('Finished running diagnosis of "%s" again.', plugin.title));
			})).then(lang.hitch(this, 'fixNoDataMessage'));
		},

		_runDiagnose: function(plugin, opts) {
			var progress = new ProgressBar();
			this.own(progress);
			var run = this.umcpProgressCommand(progress, 'diagnostic/run', lang.mixin({plugin: plugin.id}, opts));
			this._openProgressBars.push(run);
			run.then(lang.hitch(this, function(result) {
				this._grid.store.put(lang.mixin(plugin, result));
				this.refreshGrid();
			}));
			return run;
		},

		fixNoDataMessage: function() {
			if (!this._store.query(this._grid.query).length) {
				this._store.add({
					plugin: '_success_',
					success: false,
					type: 'success',
					title: _('No problems could be detected.'),
					description: ''
				});
				this.refreshGrid();
			}
		}

	});
});
