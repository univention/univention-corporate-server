<script>
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
    dismissBubble(token) {
      if (token !== undefined) {
        // remove selected bubble content
        this.$store.dispatch('notificationBubble/deleteSingleNotification', token);
      } else {
        // store modal state
        this.$store.dispatch('notificationBubble/setHideBubble');
        this.$store.dispatch('notificationBubble/showEmbedded');
      }
    },
    showNewNotification(notificationContent) {
      // for new notifications only

      this.$store.dispatch('notificationBubble/addContent', notificationContent);
      this.$store.dispatch('notificationBubble/setShowNewBubble', notificationContent);
      setTimeout(() => {
        this.$store.dispatch('notificationBubble/setHideNewBubble');
      }, 4000);
    },
    bubbleClick(e) {
      if (e.target.matches('.notification-bubble__link, .notification-bubble__link *')) {
        this.$store.dispatch('notificationBubble/hideAllNotifications');
        console.info('Bubble link clicked - TODO: add some action');
      }
    },
  },
};

export default notificationMixin;
</script>
