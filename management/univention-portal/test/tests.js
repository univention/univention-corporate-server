/*
 * Copyright 2016-2019 Univention GmbH
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
	"dojo/_base/lang",
	"dojo/_base/array",
	"dojo/_base/window",
	"dojo/dom-construct",
	"umc/tools",
	"portal"
], function(lang, array, win, domConstruct, tools, portal) {
	function log(description) {
		domConstruct.create('div', {
			innerHTML: description
		}, win.body());
	}

	var _successfulAssertions = 0;
	var _failedAssertiongs = 0;

	function assertEquals(x, y, description) {
		description = description || '';
		if (tools.isEqual(x, y)) {
			_successfulAssertions += 1;
		} else {
			log(lang.replace('FAILURE: {0} and {1} are not equal! {2}', [x, y, description]));
			_failedAssertiongs += 1; 
		}
	}

	function summary() {
		log(lang.replace('<br/> {0} successful and {1} failed tests.', [_successfulAssertions, _failedAssertiongs]));
		if (_failedAssertiongs === 0) {
			log('The tests look great :-) !');
		} else {
			log('Oh, still some work to do :-/ !');
		}
	}
	
	function testCanonicalizedIPAddresses() {
		log('<b>Testing canonicalize IP addresses...</b>');
		var _ipAddresses = [
			['1111:2222:3333:4444:5555:6666::', '1111:2222:3333:4444:5555:6666:0000:0000'],
			['1::6:77', '0001:0000:0000:0000:0000:0000:0006:0077'],
			['::11.22.33.44', '0000:0000:0000:0000:0000:0000:0b16:212c'],
			['a0a:0b0::11.22.33.44', '0a0a:00b0:0000:0000:0000:0000:0b16:212c'],
			['1.2.3.4', '0102:0304'],
			['a1a2:b1b2:0b3::', 'a1a2:b1b2:00b3:0000:0000:0000:0000:0000'],
			['2001:0DB8:0:CD30::', '2001:0DB8:0000:CD30:0000:0000:0000:0000']
		]

		array.forEach(_ipAddresses, function(i) {
			assertEquals(portal.canonicalizeIPAddress(i[0]), i[1]);
		});
	}

	function testLinkRanking() {
		log('<b>Testing link ranking...</b>');
		var _links = [[
			// description
			'Simple test with one relative link.',
			// <browserAddress>, [<possibleLink1>, ...], <bestLink>
			'http://www.example.com', ['/test'], '/test'
		], [
			'Relative links should always be preferred.',
			'http://www.example.com', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], 'https://foo.bar.com/test'
		], [
			'Relative links should always be preferred.',
			'http://www.example.com', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test', '/foobar/'], '/foobar/'
		], [
			'If browser address uses an FQDN, the FQDN address should always be taken.',
			'http://www.example.com', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], 'https://foo.bar.com/test'
		], [
			'If browser address uses an FQDN and no FQDN link is given, IPv4 should be preferred.',
			'http://www.example.com', ['//192.168.10.10/test', '//[1111::2222]/test'], '//192.168.10.10/test'
		], [
			'Relative links should always be preferred.',
			'http://192.168.10.33', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test', '/foobar/'], '/foobar/'
		], [
			'If browser address is IPv4, the IPv4 link should always be chosen.',
			'http://192.168.10.33', ['//192.177.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], '//192.177.10.10/test'
		], [
			'Amoung various IPv4 addresses, the best address match should be taken.',
			'http://192.168.10.33', ['https://192.177.10.10/test', '//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], '//192.168.10.10/test'
		], [
			'Relative links should always be preferred.',
			'http://[3333::1111:0011]', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test', '/foobar/'], '/foobar/'
		], [
			'If browser address is IPv6, the IPv6 link should be chosen.',
			'http://[3333::1111:0011]', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], '//[1111::2222]/test'
		], [
			'Among various IPv6 addresses, the best address match should be chosen.',
			'http://[3333::1111:0011]', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://[3333::2211:1122]/test', 'https://foo.bar.com/test'], 'https://[3333::2211:1122]/test'
		], [
			'A protocol relative link should always be preferred.',
			'http://www.example.com', ['//foo.bar.com/relative', 'http://foo.bar.com/http', 'https://foo.bar.com/https'], '//foo.bar.com/relative'
		], [
			'The link that matches the current protocol should be preferred.',
			'http://www.example.com', ['http://foo.bar.com/http', 'https://foo.bar.com/https'], 'http://foo.bar.com/http'
		], [
			'The link that matches the current protocol should be preferred.',
			'https://www.example.com', ['http://foo.bar.com/http', 'https://foo.bar.com/https'], 'https://foo.bar.com/https'
		], [
			'The best matching FQDN link should be taken',
			'https://slave.mydomain.local', ['https://foo.bar.com/test', '//192.111.111.111:8080/test', 'https://slave.mydomain.local/test'], 'https://slave.mydomain.local/test'
		], [
			'The port in a link should be preserved.',
			'http://192.168.10.33', ['https://192.177.10.10/test', '//192.168.10.10:8080/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], '//192.168.10.10:8080/test'
		], [
			'The port in a link should be preserved.',
			'http://[3333::1111:0011]', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://[3333::2211:1122]:8080/test', 'https://foo.bar.com/test'], 'https://[3333::2211:1122]:8080/test'
		], [
			'The query string and the fragment in a link should be preserved.',
			'http://192.168.10.33', ['https://192.177.10.10/test', '//192.168.10.10/test?key1=value1&key2=value2#fragment', '//[1111::2222]/test', 'https://foo.bar.com/test'], '//192.168.10.10/test?key1=value1&key2=value2#fragment'
		], [
			'The query string and the fragment in a link should be preserved.',
			'http://[3333::1111:0011]', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://[3333::2211:1122]/test?key1=value1&key2=value2#fragment', 'https://foo.bar.com/test'], 'https://[3333::2211:1122]/test?key1=value1&key2=value2#fragment'
		], [
			'Username and password embedded in a link should be preserved.',
			'http://192.168.10.33', ['https://192.177.10.10/test', '//user:password@192.168.10.10/test', '//[1111::2222]/test', 'https://foo.bar.com/test'], '//user:password@192.168.10.10/test'
		], [
			'Username and password embedded in a link should be preserved.',
			'http://[3333::1111:0011]', ['//192.168.10.10/test', '//[1111::2222]/test', 'https://user:password@[3333::2211:1122]/test', 'https://foo.bar.com/test'], 'https://user:password@[3333::2211:1122]/test'
		]];

		array.forEach(_links, function(i) {
			assertEquals(i[3], portal.getHighestRankedLink(i[1], i[2]), i[0]);
		});
	}

	function testConversionToLocalLink() {
		log('<b>Testing conversion to local links...</b>');
		var _links = [[
			// <description>
			'Only links referring to an FQDN can be converted.',
			// <browserHostname>, <localServerFQDN>, [<link1>, ...], [<expectedLink1>, ...]
			'192.168.2.1', 'master.mydomain.de', ['http://[1111:2222::]/test', '//192.168.3.2/test'], []
		], [
			'Only links referring to an FQDN can be converted.',
			'master.mydomain.de', 'master.mydomain.de', ['http://[1111:2222::]/test', '//192.168.3.2/test'], []
		], [
			'Relative links should be returned as local links.',
			'192.168.2.1', 'master.mydomain.de', ['http://[1111:2222::]/test', '/test', '//192.168.3.2/test'], ['/test']
		], [
			'Relative links should be returned as local links.',
			'master.mydomain.de', 'master.mydomain.de', ['http://[1111:2222::]/test', '/test', '//192.168.3.2/test'], ['/test']
		], [
			'All relative links should be returned as local links.',
			'192.168.2.1', 'master.mydomain.de', ['http://[1111:2222::]/test', '/test', '//192.168.3.2/test', '/test2'], ['/test', '/test2']
		], [
			'All relative links should be returned as local links.',
			'master.mydomain.de', 'master.mydomain.de', ['http://[1111:2222::]/test', '/test', '//192.168.3.2/test', '/test2'], ['/test', '/test2']
		], [
			'Relative links should be preferred over FQDN links.',
			'192.168.2.1', 'master.mydomain.de', ['http://[1111:2222::]/test', '/test', '//master.mydomain.de', '//192.168.3.2/test', '/test2'], ['/test', '/test2']
		], [
			'Relative links should be preferred over FQDN links.',
			'master.mydomain.de', 'master.mydomain.de', ['http://[1111:2222::]/test', '/test', '//master.mydomain.de', '//192.168.3.2/test', '/test2'], ['/test', '/test2']
		], [
			'All FQDN links returned containing the link address of the browser.',
			'192.168.2.1', 'master.mydomain.de', ['//foo.bar.com/test', 'https://master.mydomain.de/test', '//master.mydomain.de/test'], ['https://192.168.2.1/test', document.location.protocol + '//192.168.2.1/test']
		], [
			'All FQDN links returned containing the link address of the browser.',
			'foo.bar.external-host.com', 'master.mydomain.de', ['//foo.bar.com/test', 'https://master.mydomain.de/test', '//master.mydomain.de/test'], ['https://foo.bar.external-host.com/test', document.location.protocol + '//foo.bar.external-host.com/test']
		], [
			'No link will be returned if server FQDN does not match any FQDN link.',
			'192.168.2.1', 'slave.mydomain.de', ['//foo.bar.com/test', 'http://master.mydomain.de/test'], []
		], [
			'No link will be returned if server FQDN does not match any FQDN link.',
			'foo.mydomain.de', 'slave.mydomain.de', ['//foo.bar.com/test', 'http://master.mydomain.de/test'], [] 
		], [
			'The port of the original address should be preserved in the local links.',
			'192.168.2.1', 'master.mydomain.de', ['//10.200.12.12:8080/test', 'https://master.mydomain.de:8080/test'], ['https://192.168.2.1:8080/test']
		], [
			'Username and password embedded in a link should be preserved in the local links.',
			'192.168.2.1', 'master.mydomain.de', ['//user:password@10.200.12.12/test', 'https://user:password@master.mydomain.de/test'], ['https://user:password@192.168.2.1/test']
		], [
			'Query string and fragments embedded in a link should be preserved in the local links.',
			'192.168.2.1', 'master.mydomain.de', ['//10.200.12.12/test?key1=value1&key2=value2#fragment', 'https://master.mydomain.de/test?key1=value1&key2=value2#fragment'], ['https://192.168.2.1/test?key1=value1&key2=value2#fragment']
		]];

		array.forEach(_links, function(i) {
			assertEquals(i[4], portal.getLocalLinks(i[1], i[2], i[3]), i[0]);
		});
	}

	function testGetFQDNHostname() {
		// backup the original values of tools.status()
		var origStatus = tools._status;
		tools._status = {};
		tools.status('fqdn', 'another-host.mydomain.de');

		// run tests
		log('<b>Testing the conversion of links to an FQDN hostname...</b>');
		var _links = [
			[['//192.168.0.2:8080/test'], null],
			[['http://192.168.0.3/test', '//foo.bar.com:8080/test'], 'foo.bar.com'],
			[['https://10.200.1.2/test', 'https://master.mydomain.de:8080/test', 'http://master.mydomain.de:8080/test'], 'master.mydomain.de'],
			[['https://10.200.1.2/test', '/test', 'https://master.mydomain.de:8080/test', 'http://master.mydomain.de:8080/test'], tools.status('fqdn')]
		];
		array.forEach(_links, function(i) {
			assertEquals(i[1], portal.getFQDNHostname(i[0]));
		});

		// revert to the original values of tools.status()
		tools._status = origStatus;
	}

	return {
		start: function() {
			testCanonicalizedIPAddresses();
			testLinkRanking();
			testConversionToLocalLink();
			testGetFQDNHostname();
			summary();
		}
	};
});
