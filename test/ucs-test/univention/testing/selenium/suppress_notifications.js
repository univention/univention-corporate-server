/*
 * SPDX-FileCopyrightText: 2019-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
/*global define,umc*/

define([
	"dojo/_base/declare",
	"dojo/Deferred"
], function(declare, Deferred) {
	umc.dialog.contextNotify = function() {};
	umc.dialog.contextWarn = function() {};
	umc.dialog.notify = function() { return new Deferred(); };
	umc.dialog.warn = function() { return new Deferred(); };
});
