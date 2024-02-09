/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import {
  actions,
} from '@/store';

afterEach(() => {
  jest.resetAllMocks();
});

test('triggers oidc/tryLogin if keycloak url is defined', () => {
  // TODO: Use "jest.replaceProperty" once we have jest >= 27 available
  // jest.replaceProperty(process, 'env', {'VUE_APP_KEYCLOAK_URL': 'http://stub_keycloak_url.example'});
  const origVueAppKeycloakUrl = process.env.VUE_APP_KEYCLOAK_URL;
  process.env.VUE_APP_KEYCLOAK_URL = 'http://stub_keycloak_url.example';

  const actionContext = {
    dispatch: jest.fn(),
    rootGetters: {
      'user/userState': {
        authMode: 'saml',
      },
    },
  };
  actions.userIsLoggedIn(actionContext);
  expect(actionContext.dispatch).toHaveBeenCalledWith('oidc/tryLogin');

  process.env.VUE_APP_KEYCLOAK_URL = origVueAppKeycloakUrl;
});

test('does not trigger oidc/tryLogin without keycloak url', () => {
  // TODO: Use "jest.replaceProperty" once we have jest >= 27 available
  // jest.replaceProperty(process, 'env', {'VUE_APP_KEYCLOAK_URL': 'http://stub_keycloak_url.example'});
  const origVueAppKeycloakUrl = process.env.VUE_APP_KEYCLOAK_URL;
  process.env.VUE_APP_KEYCLOAK_URL = '';

  const actionContext = {
    dispatch: jest.fn(),
    rootGetters: {
      'user/userState': {
        authMode: 'saml',
      },
    },
  };
  actions.userIsLoggedIn(actionContext);
  expect(actionContext.dispatch).not.toHaveBeenCalledWith('oidc/tryLogin');

  process.env.VUE_APP_KEYCLOAK_URL = origVueAppKeycloakUrl;
});
