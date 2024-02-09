/**
 * SPDX-License-Identifier: AGPL-3.0-only
 * SPDX-FileCopyrightText: 2023-2024 Univention GmbH
 */

import Keycloak from 'keycloak-js';
import { ActionContext } from 'vuex';

import { PortalModule, RootState } from '../../root.models';

// update the token if it is going to expire in this many seconds
const UPDATE_TOKEN_SECONDS_LEFT = 5 * 60;

export type PortalActionContext<S> = ActionContext<S, RootState>;

export interface OIDC {
  // store the OIDC id and authentication tokens
  keycloak?: Keycloak,
  // timer for periodic token refresh
  timerId?: number,
}

const oidc: PortalModule<OIDC> = {

  namespaced: true,

  state: {
    keycloak: undefined,
    timerId: undefined,
  },

  mutations: {
    setTimerId(state: OIDC, timerId?: number): void {
      state.timerId = timerId;
    },

    setAuthState(state: OIDC, keycloak?: Keycloak): void {
      state.keycloak = keycloak;
    },
  },

  getters: {
    // Return the Bearer token, if OIDC login was used.
    token: (state: OIDC): string | undefined => state.keycloak?.token,

    // Timestamp when the token expires (in milliseconds)
    tokenExpiry: (state: OIDC): number | undefined => {
      // Note: token timestamp is in seconds!
      const tsSeconds = state.keycloak?.tokenParsed?.exp;
      return tsSeconds ? tsSeconds * 1e3 : undefined;
    },

    // Return the full OIDC state, for internal use.
    keycloak: (state: OIDC): Keycloak | undefined => state.keycloak,

    // Return the id of the previously started timer, if any.
    timerId: (state: OIDC): number | undefined => state.timerId,
  },

  actions: {
    /**
     * Should the token change, e.g. after login or token refresh,
     * the new Bearer token is sent to other modules that need it.
     */
    publishToken({ dispatch, getters }: PortalActionContext<OIDC>): void {
      // publish the bearer token to all modules that need it
      const token = getters.token;
      dispatch('notifications/setAuthToken', token, { root: true });
    },

    /**
     * Start a timer to refresh the OIDC token in time.
     */
    startRefreshTimer({ dispatch, commit, getters }: PortalActionContext<OIDC>): void {
      const expires: number | undefined = getters.tokenExpiry;
      if (expires) {
        // timestamps in milliseconds
        const now = new Date().getTime();
        const timeLeft = Math.max(0, expires - now - 1e3);

        // clear previous timer
        const prevId = getters.timerId;
        if (prevId) {
          clearTimeout(prevId);
          commit('setTimerId', undefined);
        }

        // start timer
        const timerId = setTimeout(() => dispatch('refreshToken'), timeLeft);
        commit('setTimerId', timerId);
      }
    },

    /**
     * Refresh the OIDC token, if needed, then return the token value.
     *
     * @returns The token in case an OIDC login happened previously, `undefined` otherwise.
     */
    async refreshToken({ dispatch, commit, getters }: PortalActionContext<OIDC>): Promise<string | undefined> {
      const keycloak: Keycloak | undefined = getters.keycloak;

      if (keycloak) {
        await keycloak
          .updateToken(UPDATE_TOKEN_SECONDS_LEFT)
          .then((_refreshed) => { // eslint-disable-line @typescript-eslint/no-unused-vars
            // This method may have been called from a timer, or not.
            // Reset the clock here to be sure either way.
            dispatch('startRefreshTimer');
          })
          .catch((err) => {
            console.log(`Token refresh failed: ${err}`);
          });
        commit('setAuthState', keycloak);
      }

      return keycloak?.token;
    },

    /**
     * Try to obtain an OIDC token from Keycloak.
     *
     * This will succeed if the user previously authenticated with Keycloak through SAML.
     * Otherwise, nothing will happen.
     */
    async tryLogin({ dispatch, commit }: PortalActionContext<OIDC>): Promise<void> {
      const keycloak = new Keycloak({
        realm: process.env.VUE_APP_KEYCLOAK_REALM || 'ucs',
        url: process.env.VUE_APP_KEYCLOAK_URL,
        clientId: 'portal-frontend',
      });

      await keycloak.init({
        onLoad: 'check-sso',
        // TODO: Consider enabling the hidden iFrame to support single sign-out.
        //       https://git.knut.univention.de/univention/components/univention-portal/-/issues/687
        // checkLoginIframe: true,
        silentCheckSsoRedirectUri: `${document.location.origin}/univention/portal/oidc/silent.html`,
      })
        .then((authenticated) => {
          if (authenticated) {
            // authentication succeeded, now start the token refresh timer
            console.log('User authenticated via OIDC');
            commit('setAuthState', keycloak);
            dispatch('publishToken');
            dispatch('startRefreshTimer');
          } else {
            console.error('User NOT authenticated via OIDC');
          }
        })
        .catch((error) => {
          console.error(`OIDC authentication failed: ${error}`);
        });
    },

    /**
     * Logout from Keycloak.
     *
     * This will succeed if the user previously authenticated with Keycloak through SAML.
     * Otherwise, nothing will happen.
     */
    async tryLogout({ commit, getters }: PortalActionContext<OIDC>): Promise<void> {
      const keycloak: Keycloak | undefined = getters.keycloak;
      if (keycloak) {
        await keycloak.logout();
        commit('setAuthState', keycloak);
      }
    },
  },
};

export default oidc;
