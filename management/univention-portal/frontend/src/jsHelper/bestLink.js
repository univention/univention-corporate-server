/*
 * Copyright 2021-2022 Univention GmbH
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
import { isFQDN, isIPv4Address, isIPv6Address } from '@/jsHelper/tools';

// convert IPv6 addresses to their canonical form:
//   ::1:2 -> 0000:0000:0000:0000:0000:0000:0001:0002
//   1111:2222::192.168.1.1 -> 1111:2222:0000:0000:0000:0000:c0a8:0101
// but this can also be used for IPv4 addresses:
//   192.168.1.1 -> c0a8:0101
function canonicalizeIPAddress(_address) {
  if (isFQDN(_address)) {
    return _address;
  }

  // remove leading and trailing ::
  const address = _address.replace(/^:|:$/g, '');

  // split address into 2-byte blocks
  let parts = address.split(':');

  // replace IPv4 address inside IPv6 address
  if (isIPv4Address(parts[parts.length - 1])) {
    // parse bytes of IPv4 address
    const ipv4Parts = parts[parts.length - 1].split('.').map((part) => parseInt(part, 10).toString(16));

    // remove IPv4 address and append bytes in IPv6 style
    parts.splice(-1, 1);
    parts.push(ipv4Parts[0] + ipv4Parts[1]);
    parts.push(ipv4Parts[2] + ipv4Parts[3]);
  }

  // expand grouped zeros "::"
  const iEmptyPart = parts.indexOf('');
  if (iEmptyPart >= 0) {
    parts.splice(iEmptyPart, 1);
    while (parts.length < 8) {
      parts.splice(iEmptyPart, 0, '0');
    }
  }

  // add leading zeros
  parts = parts.map((ipart) => ipart.padStart(4, 0));

  return parts.join(':');
}

function getAnchorElement(uri) {
  const linkElement = document.createElement('a');
  linkElement.setAttribute('href', uri);
  return linkElement;
}

function getURIHostname(uri) {
  return getAnchorElement(uri).hostname.replace(/^\[|\]$/g, '');
}

function getAddressType(link) {
  if (isFQDN(link)) {
    return 'fqdn';
  }
  if (isIPv6Address(link)) {
    return 'ipv6';
  }
  if (isIPv4Address(link)) {
    return 'ipv4';
  }
  return '';
}

function getProtocolType(link) {
  if (link.indexOf('//') === 0) {
    return 'relative';
  }
  if (link.indexOf('https') === 0) {
    return 'https';
  }
  if (link.indexOf('http') === 0) {
    return 'http';
  }
  return '';
}

const regExpRelativeLink = /^\/([^/].*)?$/;
function isRelativeLink(link) {
  return regExpRelativeLink.test(link);
}

// return 1 if link is a relative link, otherwise 0
function scoreRelativeURI(link) {
  return link.indexOf('/') === 0 && link.indexOf('//') !== 0 ? 1 : 0;
}

// score according to the following matrix
//               Browser address bar
//              | FQDN | IPv4 | IPv6
//       / FQDN |  4   |  1   |  1
// link <  IPv4 |  2   |  4   |  2
//       \ IPv6 |  1   |  2   |  4
function scoreAddressType(browserLinkType, linkType) {
  const scores = {
    fqdn: { fqdn: 4, ipv4: 2, ipv6: 1 },
    ipv4: { fqdn: 1, ipv4: 4, ipv6: 2 },
    ipv6: { fqdn: 1, ipv4: 2, ipv6: 4 },
  };
  try {
    return scores[browserLinkType][linkType] || 0;
  } catch (err) {
    return 0;
  }
}

// score according to the following matrix
//              Browser address bar
//               | https | http
//       / "//"  |   4   |  4
// link <  https |   2   |  1
//       \ http  |   1   |  2
function scoreProtocolType(browserProtocolType, protocolType) {
  const scores = {
    https: { relative: 4, https: 2, http: 1 },
    http: { relative: 4, https: 1, http: 2 },
  };
  try {
    return scores[browserProtocolType][protocolType] || 0;
  } catch (err) {
    return 0;
  }
}

// score is computed as the number of matched characters
function scoreAddressMatch(_browserHostname, _hostname, matchBackwards) {
  let browserHostname = _browserHostname;
  let hostname = _hostname;
  if (matchBackwards) {
    // match not from the beginning of the string, but from the end
    browserHostname = browserHostname.split('').reverse()
      .join('');
    hostname = hostname.split('').reverse()
      .join('');
  }
  let i;
  for (i = 0; i < Math.min(browserHostname.length, hostname.length); i += 1) {
    if (browserHostname[i] !== hostname[i]) {
      break;
    }
  }
  return i;
}

// Given the browser URI and a list of links, each link is ranked via a
// multi-part score. This effectively allows to chose the best matching
// link w.r.t. the browser session.
function rankLinks(browserURI, _links) {
  // score all links
  const browserHostname = getURIHostname(browserURI);
  const browserLinkType = getAddressType(browserHostname);
  const canonicalizedBrowserHostname = canonicalizeIPAddress(browserHostname);
  const browserProtocolType = getProtocolType(browserURI);
  const links = _links.map((ilink) => {
    const linkHostname = getURIHostname(ilink);
    const canonicalizedLinkHostname = canonicalizeIPAddress(linkHostname);
    const linkType = getAddressType(linkHostname);
    const linkProtocolType = getProtocolType(ilink);
    let addressMatchScore = 0;
    if (browserLinkType === linkType) {
      // FQDNs are matched backwards, IP addresses forwards
      const matchBackwards = linkType === 'fqdn';
      addressMatchScore = scoreAddressMatch(canonicalizedBrowserHostname, canonicalizedLinkHostname, matchBackwards);
    }
    return {
      scores: [
        scoreRelativeURI(ilink),
        addressMatchScore,
        scoreAddressType(browserLinkType, linkType),
        scoreProtocolType(browserProtocolType, linkProtocolType),
      ],
      link: ilink,
    };
  });

  function cmp(x, y) {
    for (let i = 0; i < x.scores.length; i += 1) {
      if (x.scores[i] < y.scores[i]) {
        return 1;
      }
      if (x.scores[i] > y.scores[i]) {
        return -1;
      }
    }
    return 0;
  }

  // sort links descending w.r.t. their scores
  links.sort(cmp);

  // return the best match
  return links;
}

function getHighestRankedLink(browserURI, links) {
  return rankLinks(browserURI, links)[0].link || '#';
}

function getLocalLinks(browserHostname, serverFQDN, links) {
  // check whether there is any relative link
  const relativeLinks = links.filter((ilink) => isRelativeLink(ilink));
  if (relativeLinks.length) {
    return relativeLinks;
  }

  // check whether there is a link containing the FQDN of the local server
  const localLinks = [];
  links.forEach((ilink) => {
    const uri = getAnchorElement(ilink);
    if (uri.hostname === serverFQDN) {
      uri.hostname = browserHostname;
      localLinks.push(uri.href);
    }
  });
  return localLinks;
}

export default function main(links, fqdn, locale) {
  const localizedLinks = {};
  links.forEach((link) => {
    const alreadyFoundLinks = localizedLinks[link.locale] || [];
    alreadyFoundLinks.push(link.value);
    localizedLinks[link.locale] = alreadyFoundLinks;
  });
  const usedLinks = localizedLinks[locale] || localizedLinks.en_US || [];
  if (usedLinks.length === 0) {
    return '';
  }
  const browserHostname = getURIHostname(document.location.href);
  // get the best link to be displayed
  const localLinks = getLocalLinks(browserHostname, fqdn, usedLinks).concat(usedLinks);
  const bestLink = getHighestRankedLink(document.location.href, localLinks);

  // get the hostname to be displayed on the tile
  return bestLink;
}
