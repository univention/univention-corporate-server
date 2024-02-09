/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import Keycloak from 'keycloak-js';
import { createStubStore } from './stubs';

jest.mock('keycloak-js');

describe('oidc', () => {

  beforeEach(() => {
    (Keycloak as jest.Mock).mockClear();
  });

  it('regularly refreshes the token', async () => {
    // fix the date to now
    const mockDate = new Date();
    jest.spyOn(window, 'Date').mockImplementation(() => mockDate as unknown as string);

    const mockSetTimeout = jest.spyOn(window, 'setTimeout');
    const mockClearTimeout = jest.spyOn(window, 'clearTimeout');

    // fake token expiry
    const timeLeft = 10e3;
    const stubNow = mockDate.getTime();
    const stubExp = stubNow + timeLeft;

    (Keycloak as jest.Mock).mockImplementation(() => ({
      token: 'foo',
      tokenParsed: {
        exp: stubExp / 1e3,
      },
      updateToken: jest.fn().mockImplementation(() => Promise.resolve(false)),
      init: jest.fn().mockImplementation(() => Promise.resolve(true)),
    }));

    // just set our fake Keycloak state
    const stubStore = createStubStore();
    stubStore.commit('oidc/setAuthState', new Keycloak());

    // now start the timer
    await stubStore.dispatch('oidc/startRefreshTimer');
    expect(mockSetTimeout.mock.calls.length).toBe(1);
    expect(mockSetTimeout.mock.calls[0][1]).toBeLessThanOrEqual(timeLeft);

    // start the timer again, this should clear the previous timer
    await stubStore.dispatch('oidc/startRefreshTimer');
    expect(mockClearTimeout).toHaveBeenCalledTimes(1);
    expect(mockSetTimeout).toHaveBeenCalledTimes(2);
  });

  it('stores the refreshed token in the store', async () => {
    const stubToken = 'foo';
    (Keycloak as jest.Mock).mockImplementation(() => ({
      token: stubToken,
      updateToken: jest.fn().mockImplementation(() => Promise.resolve(true)),
      init: jest.fn().mockImplementation(() => Promise.resolve(true)),
    }));

    const stubStore = createStubStore();
    await stubStore.dispatch('oidc/tryLogin');
    expect(stubStore.getters['oidc/token']).toEqual(stubToken);

    await stubStore.dispatch('oidc/refreshToken');
    expect(stubStore.getters['oidc/token']).toEqual(stubToken);
  });

  it('returns the token after refreshing it', async () => {
    const stubToken = 'foo';
    (Keycloak as jest.Mock).mockImplementation(() => ({
      token: stubToken,
      updateToken: jest.fn().mockImplementation(() => Promise.resolve(false)),
      init: jest.fn().mockImplementation(() => Promise.resolve(true)),
    }));

    const stubStore = createStubStore();
    const storeDispatch = jest.spyOn(stubStore, 'dispatch');

    await stubStore.dispatch('oidc/tryLogin');

    const token = await stubStore.dispatch('oidc/refreshToken');
    expect(storeDispatch).toHaveBeenCalledWith('oidc/startRefreshTimer', undefined);
    expect(token).toEqual(stubToken);
  });

  it('adds the OIDC token to the store', async () => {
    const stubToken = 'foo';
    (Keycloak as jest.Mock).mockImplementation(() => ({
      token: stubToken,
      updateToken: jest.fn().mockImplementation(() => Promise.resolve(false)),
      init: jest.fn().mockImplementation(() => Promise.resolve(true)),
    }));

    const stubStore = createStubStore();
    const storeDispatch = jest.spyOn(stubStore, 'dispatch');

    await stubStore.dispatch('oidc/tryLogin');

    expect(stubStore.getters['oidc/token']).toEqual(stubToken);
    expect(stubStore.getters['notifications/token']).toEqual(stubToken);
    expect(storeDispatch).toHaveBeenCalledWith('oidc/startRefreshTimer', undefined);
  });

});
