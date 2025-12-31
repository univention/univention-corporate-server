/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
// taken from: http://stackoverflow.com/a/9221063
const regIPv4 = /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))$/;
const regIPv6 = /^((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?$/;

const regFQDN = /^(?=.{1,254}$)((?=[a-z0-9-]{1,63}\.)[a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,63}$/i;

function isIPv4Address(ip: string): boolean {
  return regIPv4.test(ip);
}

function isIPv6Address(ip: string): boolean {
  return regIPv6.test(ip);
}

function isFQDN(fqdn: string): boolean {
  return regFQDN.test(fqdn);
}

function getCookie(name: string): string | undefined {
  const cookies = {};
  document.cookie.split('; ').forEach((cookieWithValue) => {
    const idx = cookieWithValue.indexOf('=');
    const cookieName = cookieWithValue.slice(0, idx);
    const value = cookieWithValue.slice(idx + 1);
    cookies[cookieName] = value;
  });
  return cookies[name];
}

const cookiePath = process.env.VUE_APP_COOKIE_PATH || '/univention/';

function setCookie(name: string, value: string, path?: string, domain?: string): void {
  const date = new Date();
  date.setTime(date.getTime() + (100 * 24 * 60 * 60 * 1000)); // 100 days
  document.cookie = `${name}=${value}; expires=${date.toUTCString()}; domain=${domain || document.domain}; path=${path || cookiePath}; SameSite=Strict`;
}

function setInvalidity(element: any, name: string, invalid: boolean): void {
  const el = element.$refs[name] as HTMLElement;
  if (invalid) {
    el.setAttribute('invalid', 'invalid');
  } else {
    el.removeAttribute('invalid');
  }
}

function randomId(): string {
  return Math.random().toString(36)
    .substr(2);
}

export { isFQDN, isIPv6Address, isIPv4Address, getCookie, setCookie, setInvalidity, randomId };
