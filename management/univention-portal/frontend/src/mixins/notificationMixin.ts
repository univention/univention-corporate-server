import { store } from '@/store';
import { mapGetters } from 'vuex';

const notificationMixin = {
  computed: {
    ...mapGetters({
      bubbleState: 'notificationBubble/bubbleState',
      bubbleStateStandalone: 'notificationBubble/bubbleStateStandalone',
      bubbleStateNewBubble: 'notificationBubble/bubbleStateNewBubble',
      bubbleContent: 'notificationBubble/bubbleContent',
      bubbleContentNewNotification: 'notificationBubble/bubbleContentNewNotification',
    }),
  },
  methods: {
    dismissBubble(token): void {
      if (token !== undefined) {
        // remove selected bubble content
        store.dispatch('notificationBubble/deleteSingleNotification', token);
      } else {
        // store modal state
        store.dispatch('notificationBubble/setHideBubble');
        store.dispatch('notificationBubble/showEmbedded');
      }
    },
    showNewNotification(notificationContent): void {
      // for new notifications only

      store.dispatch('notificationBubble/addContent', notificationContent);
      store.dispatch('notificationBubble/setShowNewBubble', notificationContent);
      setTimeout(() => {
        store.dispatch('notificationBubble/setHideNewBubble');
      }, 4000);
    },
    bubbleClick(e): void {
      if (e.target.matches('.notification-bubble__link, .notification-bubble__link *')) {
        store.dispatch('notificationBubble/hideAllNotifications');
        console.info('Bubble link clicked - TODO: add some action');
      }
    },
  },
};

export default notificationMixin;
