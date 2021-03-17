// vue
import axios from 'axios';
import { InjectionKey } from 'vue';
import { createStore, Store, useStore as baseUseStore } from 'vuex';
// modules
import categories from './modules/categories';
import locale from './modules/locale';
import menu from './modules/menu';
import meta from './modules/meta';
import modal from './modules/modal';
import navigation from './modules/navigation';
import notificationBubble from './modules/notificationBubble';
import portalData from './modules/portalData';
import search from './modules/search';
import tabs from './modules/tabs';
import user from './modules/user';
import { RootState } from './types';

// get env vars
const portalUrl = process.env.VUE_APP_PORTAL_URL || '';
const portalJson = process.env.VUE_APP_PORTAL_DATA || './portal.json';
const portalMeta = process.env.VUE_APP_META_DATA || '/univention/meta.json';

export const key: InjectionKey<Store<RootState>> = Symbol('');

export const store = createStore<RootState>({
  modules: {
    categories,
    locale,
    modal,
    navigation,
    notificationBubble,
    portalData,
    user,
    menu,
    tabs,
    search,
    meta,
  },
  strict: process.env.NODE_ENV !== 'production',
  state: {
    // Just a sample property, the RootState should not be empty
    version: '1.0.0',
  },
  mutations: {},
  actions: {
    loadPortal: () => {
      store.dispatch('modal/setShowLoadingModal');

      // display standalone notification bubbles
      if (store.getters['notificationBubble/bubbleContent'].length > 0) {
        store.dispatch('notificationBubble/setShowBubble');
      }

      return new Promise<unknown>((resolve) => {
        // store portal data
        console.log('Loading Portal');

        // get meta data
        axios.get(`${portalUrl}${portalMeta}`).then(
          (response) => {
            const metaData = response.data;
            store.dispatch('meta/setMeta', metaData);
          }, (error) => {
            console.error(error);
          },
        );

        // get portal data
        axios.get(`${portalUrl}${portalJson}`).then(
          (response) => {
            const PortalData = response.data;
            store.dispatch('menu/setMenu', PortalData);
            store.dispatch('portalData/setPortal', PortalData);
            store.dispatch('categories/setOriginalArray', PortalData);
            store.dispatch('user/setUser', {
              user: {
                username: PortalData.username,
                displayName: PortalData.user_displayname,
                mayEditPortal: PortalData.may_edit_portal,
                mayLoginViaSAML: PortalData.may_login_via_saml,
              },
            });
            store.dispatch('modal/setHideModal');
            resolve(PortalData);
          }, () => {
            store.dispatch('modal/setHideModal');
            resolve({});
          },
        );
      });
    },
  },
  getters: {},
});

// Define your own `useStore` composition function
export function useStore(): Store<RootState> {
  return baseUseStore(key);
}
