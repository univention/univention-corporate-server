import { Module } from 'vuex';

interface Notification {
  bubbleTitle: string;
  bubbleDescription: string;
}

interface WeightedNotification extends Notification {
  bubbleImportance: string;
}

interface FullNotification extends WeightedNotification {
  bubbleToken: string;
}

export interface State {
  visible: boolean;
  visibleStandalone: boolean;
  visibleNew: boolean;
  content: Array<FullNotification>;
  contentOfNewNotification: Array<FullNotification>;
}

const bubble: Module<State, unknown> = {
  namespaced: true,
  state: {
    visible: false,
    visibleStandalone: false,
    visibleNew: false,
    content: [],
    contentOfNewNotification: [],
  },

  mutations: {
    WRITE_CONTENT(state, payload) {
      state.content = payload;
    },
    ADD_CONTENT(state: State, notification: FullNotification) {
      state.contentOfNewNotification = [];
      state.content.push(notification);
      state.contentOfNewNotification.push(notification);
    },
    SHOW(state) {
      state.visibleStandalone = true;
    },
    SHOW_NEW(state) {
      state.visibleNew = true;
    },
    SHOW_EMBEDDED(state) {
      state.visible = true;
      state.visibleStandalone = false;
      state.visibleNew = false;
    },
    HIDE(state) {
      state.visibleStandalone = false;
    },
    HIDE_NEW_NOTIFICATION(state) {
      state.visibleNew = false;
    },
    HIDE_ALL_NOTIFICATIONS(state) {
      state.visible = false;
      state.visibleStandalone = false;
      state.visibleNew = false;
    },
    DELETE_SINGLE_NOTIFICTION(state, token) {
      const indexContent = state.content.findIndex((notification) => notification.bubbleToken === token);
      const indexNewNotification = state.contentOfNewNotification.findIndex((notification) => notification.bubbleToken === token);
      state.content.splice(indexContent, 1);
      state.contentOfNewNotification.splice(indexNewNotification, 1);
    },
  },

  getters: {
    bubbleState: (state) => state.visible,
    bubbleStateStandalone: (state) => state.visibleStandalone,
    bubbleStateNewBubble: (state) => state.visibleNew,
    bubbleContent: (state) => state.content,
    bubbleContentNewNotification: (state) => state.contentOfNewNotification,
  },

  actions: {
    setShowBubble({ commit }, payload) {
      commit('SHOW', payload);
    },
    setShowNewBubble({ commit }, payload) {
      commit('SHOW_NEW', payload);
    },
    setHideBubble({ commit }, payload) {
      commit('HIDE', payload);
    },
    setHideNewBubble({ commit }) {
      commit('HIDE_NEW_NOTIFICATION');
    },
    setContent({ commit }, payload) {
      commit('WRITE_CONTENT', payload);
    },
    addContent({ commit }, item: WeightedNotification) {
      commit('ADD_CONTENT', { ...item, bubbleToken: Math.random() });
      commit('SHOW_NEW');
    },
    addNotification({ dispatch }, item: Notification) {
      dispatch('addContent', { ...item, bubbleImportance: 'neutral' });
    },
    hideAllNotifications({ commit }, payload) {
      commit('HIDE_ALL_NOTIFICATIONS', payload);
    },
    showEmbedded({ commit }, payload) {
      commit('SHOW_EMBEDDED', payload);
    },
    deleteSingleNotification({ commit }, token) {
      commit('DELETE_SINGLE_NOTIFICTION', token);
    },
  },
};

export default bubble;
