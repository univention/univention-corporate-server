#!/usr/bin/node
/*
 * SPDX-FileCopyrightText: 2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const appCenterJs = path.resolve(__dirname, '../../umc/js/appcenter');

function declare(_name, _bases, properties) {
	function Declared(options) {
		Object.assign(this, options);
	}
	Declared.prototype = Object.assign({
		inherited() {},
	}, properties);
	Declared.prototype.constructor = Declared;
	return Declared;
}

function translate(message, ...values) {
	let index = 0;
	return message.replace(/%s/g, () => String(values[index++]));
}

function loadAmdModule(filename, dependencies) {
	let exported;
	const source = fs.readFileSync(path.join(appCenterJs, filename), 'utf8');
	const context = {
		Array,
		console,
		Infinity,
		Object,
		Promise,
		define(names, factory) {
			exported = factory(...names.map(name => dependencies[name]));
		},
	};
	vm.runInNewContext(source, context, {filename});
	return exported;
}

function encode(value) {
	return value
		.replaceAll('&', '&amp;')
		.replaceAll('<', '&lt;')
		.replaceAll('>', '&gt;');
}

class Deferred {
	constructor() {
		this.promise = new Promise((resolve, reject) => {
			this._resolve = resolve;
			this._reject = reject;
		});
	}

	resolve(value) {
		this._resolve(value);
	}

	reject(error) {
		this._reject(error);
	}

	then(...args) {
		return this.promise.then(...args);
	}
}

class ProgressBar {
	reset() {}
	setInfo() {}
	getErrors() {
		return {errors: []};
	}
	_addErrors() {}
}

function loadPostInstallWizard() {
	return loadAmdModule('AppPostInstallWizard.js', {
		'dojo/_base/declare': declare,
		'dojo/_base/array': {},
		'dojo/_base/lang': {},
		'dojo/dom-class': {},
		'dojo/on': () => {},
		'dojox/html/entities': {encode},
		'dijit/layout/ContentPane': function() {},
		'umc/widgets/ContainerWidget': function() {},
		'umc/widgets/Text': function() {},
		'umc/widgets/Wizard': function() {},
		'./AppText': function() {},
		'./AppDetailsContainer': function() {},
		'./AppInstallWizardReadmeInstallPage': {getPageConf: () => null},
		'put-selector/put': () => {},
		'umc/i18n!umc/modules/appcenter': translate,
	});
}

function loadChooseHostWizard() {
	return loadAmdModule('AppChooseHostWizard.js', {
		'dojo/_base/declare': declare,
		'dojo/_base/array': {forEach: (values, callback) => values.forEach(callback)},
		'dojo/dom-class': {add() {}},
		'dojox/html/entities': {encode},
		'dijit/_WidgetBase': function() {},
		'dijit/_TemplatedMixin': function() {},
		'umc/widgets/ComboBox': function() {},
		'umc/widgets/Text': function() {},
		'umc/widgets/Wizard': function() {},
		'./AppText': {
			appFromApp: app => app,
		},
		'umc/i18n!umc/modules/appcenter': translate,
	});
}

function loadInstallDialog(tools) {
	return loadAmdModule('AppInstallDialog.js', {
		'dojo/_base/declare': declare,
		'dojo/_base/lang': {},
		'dojo/_base/array': {map: (values, callback) => values.map(callback)},
		'dojo/dom-class': {add() {}},
		'dojo/topic': {},
		'dojo/on': () => {},
		'dojo/Deferred': Deferred,
		'dojo/promise/all': Promise.all,
		'umc/tools': tools,
		'umc/widgets/Page': function() {},
		'umc/widgets/ProgressBar': ProgressBar,
		'./App': function(app) { Object.assign(this, app); },
		'./AppChooseHostWizard': function() {},
		'./AppInstallWizard': function() {},
		'./AppPostInstallWizard': function() {},
		'./_AppDialogMixin': function() {},
		'umc/i18n!umc/modules/appcenter': translate,
	});
}

function testSuccessfulMultiAppSummary() {
	const AppPostInstallWizard = loadPostInstallWizard();
	const wizard = new AppPostInstallWizard({
		action: 'install',
		apps: [
			{id: 'provisioning-service', name: 'Provisioning & Service'},
			{id: 'ox-connector', name: 'OX <Connector>'},
		],
		errorMessages: [],
		result: {
			'primary.example.test': {
				'provisioning-service': {success: true},
			},
			'member.example.test': {
				'ox-connector': {success: true},
			},
		},
	});
	wizard.postMixInProperties();

	assert.equal(wizard.pages.length, 1);
	const successPage = wizard.pages[0];
	assert.equal(successPage.name, 'success');
	assert.equal(successPage.helpText, 'The following Apps were installed successfully:');
	assert.match(successPage.widgets[0].content, /Provisioning &amp; Service on primary\.example\.test/);
	assert.match(successPage.widgets[0].content, /OX &lt;Connector&gt; on member\.example\.test/);

	wizard.getPage = () => ({set() {}});
	wizard.postCreate();
	assert.equal(wizard.needsToBeShown, true);
}

function testSingleAppSummaryAndFallbackName() {
	const AppPostInstallWizard = loadPostInstallWizard();
	const wizard = new AppPostInstallWizard({
		action: 'install',
		apps: [],
		errorMessages: [],
		result: {
			'member.example.test': {
				'unknown-app': {success: true},
			},
		},
	});
	wizard.postMixInProperties();

	assert.equal(wizard.pages[0].helpText, 'The following App was installed successfully:');
	assert.match(wizard.pages[0].widgets[0].content, /unknown-app on member\.example\.test/);
}

function testMixedResultShowsFailuresAndSuccessfulAppsSeparately() {
	const AppPostInstallWizard = loadPostInstallWizard();
	const wizard = new AppPostInstallWizard({
		action: 'install',
		apps: [
			{id: 'failed-app', name: 'Failed App'},
			{id: 'successful-app', name: 'Successful App'},
		],
		errorMessages: ['The failed App returned an error'],
		result: {
			'primary.example.test': {
				'failed-app': {success: false},
			},
			'member.example.test': {
				'successful-app': {success: true},
			},
		},
	});
	wizard.postMixInProperties();

	assert.equal(wizard.hasErrors, true);
	assert.equal(wizard.pages.map(page => page.name).join(','), 'failures,success');
	assert.match(wizard.pages[0].helpText, /failed-app on primary\.example\.test/);
	const successContent = wizard.pages[1].widgets[0].content;
	assert.match(successContent, /Successful App on member\.example\.test/);
	assert.doesNotMatch(successContent, /Failed App/);
	assert.doesNotMatch(successContent, /failed-app/);
}

function testEmptyAndPartialResultsDoNotInventSuccessfulApps() {
	const AppPostInstallWizard = loadPostInstallWizard();
	const emptyWizard = new AppPostInstallWizard({
		action: 'install',
		apps: [{id: 'missing-app', name: 'Missing App'}],
		errorMessages: [],
		result: {},
	});
	emptyWizard.postMixInProperties();
	assert.equal(emptyWizard.pages.length, 0);
	emptyWizard.postCreate();
	assert.equal(emptyWizard.needsToBeShown, false);

	const partialWizard = new AppPostInstallWizard({
		action: 'install',
		apps: [
			{id: 'reported-app', name: 'Reported App'},
			{id: 'missing-app', name: 'Missing App'},
		],
		errorMessages: [],
		result: {
			'member.example.test': {
				'reported-app': {success: true},
			},
		},
	});
	partialWizard.postMixInProperties();
	assert.equal(partialWizard.pages.length, 1);
	assert.equal(partialWizard.pages[0].helpText, 'The following App was installed successfully:');
	const successContent = partialWizard.pages[0].widgets[0].content;
	assert.match(successContent, /Reported App on member\.example\.test/);
	assert.doesNotMatch(successContent, /Missing App/);
}

function installationData(fqdn, displayName) {
	return {
		fqdn,
		displayName,
		canInstall: () => true,
		isLocal: () => false,
	};
}

function testRequiredHostIsShownAndLocked() {
	const AppChooseHostWizard = loadChooseHostWizard();
	const wizard = new AppChooseHostWizard({
		apps: [{
			id: 'provisioning-service',
			name: 'Provisioning Service',
			installationData: [
				installationData('primary.example.test', 'Primary'),
				installationData('member.example.test', 'Member'),
			],
		}, {
			id: 'ox-connector',
			name: 'OX Connector',
			installationData: [installationData('member.example.test', 'Member')],
		}],
		auto_installed: ['provisioning-service'],
		required_hosts: {
			'provisioning-service': ['primary.example.test'],
		},
	});
	wizard.postMixInProperties();

	const chooseHostPage = wizard.pages.find(page => page.name === 'chooseHosts');
	const provisioningHost = chooseHostPage.widgets.find(widget => widget.name === 'provisioning-service');
	assert.equal(provisioningHost.disabled, true);
	assert.equal(provisioningHost.value, 'primary.example.test');
	assert.equal(provisioningHost.staticValues.length, 1);
	assert.equal(provisioningHost.staticValues[0].id, 'primary.example.test');
	assert.equal(wizard.isPageVisible('chooseHosts'), true);
}

function testMalformedRequiredHostMappingIsRejected() {
	const AppChooseHostWizard = loadChooseHostWizard();
	const wizard = new AppChooseHostWizard({
		apps: [{
			id: 'provisioning-service',
			name: 'Provisioning Service',
			installationData: [],
		}],
		auto_installed: ['provisioning-service'],
		required_hosts: {
			'provisioning-service': ['primary.example.test', 'backup.example.test'],
		},
	});
	assert.throws(
		() => wizard.postMixInProperties(),
		/Invalid required host mapping for App provisioning-service/
	);
}

function testIneligibleRequiredHostLeavesTheFormInvalid() {
	const AppChooseHostWizard = loadChooseHostWizard();
	const wizard = new AppChooseHostWizard({
		apps: [{
			id: 'provisioning-service',
			name: 'Provisioning Service',
			installationData: [installationData('member.example.test', 'Member')],
		}],
		auto_installed: ['provisioning-service'],
		required_hosts: {
			'provisioning-service': ['primary.example.test'],
		},
	});
	wizard.postMixInProperties();
	const chooseHostPage = wizard.pages.find(page => page.name === 'chooseHosts');
	const provisioningHost = chooseHostPage.widgets.find(widget => widget.name === 'provisioning-service');
	assert.equal(provisioningHost.required, true);
	assert.equal(provisioningHost.disabled, false);
	assert.equal(provisioningHost.value, undefined);
	assert.equal(provisioningHost.staticValues.length, 0);
	const explanation = chooseHostPage.widgets.find(widget => widget.name === 'chooseHosts_removeExplanation_provisioning-service');
	assert.match(explanation.content, /required host primary\.example\.test is not available/);
}

async function testRequiredHostsAreWiredAndMerged() {
	const tools = {
		umcpCommand: () => Promise.resolve({
			result: {
				apps: [{id: 'ox-connector'}],
				auto_installed: [],
				required_hosts: {'provisioning-service': ['primary.example.test']},
				settings: {},
			},
		}),
	};
	const AppInstallDialog = loadInstallDialog(tools);
	const dialog = new AppInstallDialog({standbyDuring() {}});
	const backpack = await dialog._resolveApps({
		action: 'install',
		apps: [],
	});
	assert.equal(backpack.required_hosts['provisioning-service'][0], 'primary.example.test');

	dialog._setHosts(backpack, {
		'ox-connector': 'member.example.test',
		'provisioning-service': 'member.example.test',
	});
	assert.equal(backpack.hosts['member.example.test'][0], 'ox-connector');
	assert.equal(backpack.hosts['member.example.test'].length, 1);
	assert.equal(backpack.hosts['primary.example.test'][0], 'provisioning-service');

	assert.throws(
		() => dialog._addRequiredHosts({
			hosts: {},
			required_hosts: {
				'provisioning-service': ['primary.example.test', 'backup.example.test'],
			},
		}),
		/Invalid required host mapping for App provisioning-service/
	);
}

async function testResolveRejectionIsPreserved() {
	const expectedError = new Error('dependency resolution failed');
	const tools = {
		umcpCommand: () => Promise.reject(expectedError),
	};
	const AppInstallDialog = loadInstallDialog(tools);
	const dialog = new AppInstallDialog({standbyDuring() {}});
	const outcome = await Promise.race([
		dialog._resolveApps({action: 'install', apps: []}).then(
			() => ({resolved: true}),
			error => ({error})
		),
		new Promise(resolve => setTimeout(() => resolve({timedOut: true}), 50)),
	]);
	assert.equal(outcome.timedOut, undefined);
	assert.equal(outcome.resolved, undefined);
	assert.equal(outcome.error, expectedError);
}

async function testRunRejectionIsPreserved() {
	const expectedError = new Error('backend failed');
	const tools = {
		umcpProgressCommand: () => Promise.reject(expectedError),
	};
	const AppInstallDialog = loadInstallDialog(tools);
	const dialog = new AppInstallDialog({
		standbyDuring() {},
	});
	const backpack = {
		action: 'install',
		apps: [{id: 'ox-connector'}],
		appSettings: {'ox-connector': {}},
		autoInstalled: [],
		hosts: {'member.example.test': ['ox-connector']},
	};

	await assert.rejects(dialog._run(backpack), error => error === expectedError);
}

async function main() {
	testSuccessfulMultiAppSummary();
	testSingleAppSummaryAndFallbackName();
	testMixedResultShowsFailuresAndSuccessfulAppsSeparately();
	testEmptyAndPartialResultsDoNotInventSuccessfulApps();
	testRequiredHostIsShownAndLocked();
	testMalformedRequiredHostMappingIsRejected();
	testIneligibleRequiredHostLeavesTheFormInvalid();
	await testRequiredHostsAreWiredAndMerged();
	await testResolveRejectionIsPreserved();
	await testRunRejectionIsPreserved();
	console.log('App Center install frontend tests passed');
}

main().catch(error => {
	console.error(error);
	process.exitCode = 1;
});
