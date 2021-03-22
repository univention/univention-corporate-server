<!--
 * Copyright 2021 Univention GmbH
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
-->
<script>
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
      getActiveButton: 'navigation/getActiveButton',
    }),
  },
  methods: {
    dismissBubble(token) {
      if (token !== undefined) {
        // remove selected bubble content
        store.dispatch('notificationBubble/deleteSingleNotification', token);
      } else {
        // store modal state
        store.dispatch('notificationBubble/setHideBubble');
        store.dispatch('notificationBubble/showEmbedded');
      }
      if (token === this.getActiveButton) {
        if (document.getElementById('loginButton')) {
          document.getElementById('loginButton').focus();
        }
      }
    },
    showNewNotification(notificationContent) {
      // for new notifications only

      store.dispatch('notificationBubble/addContent', notificationContent);
      store.dispatch('notificationBubble/setShowNewBubble', notificationContent);
      setTimeout(() => {
        store.dispatch('notificationBubble/setHideNewBubble');
      }, 4000);
    },
    bubbleClick(e) {
      if (e.target.matches('.notification-bubble__link, .notification-bubble__link *')) {
        store.dispatch('notificationBubble/hideAllNotifications');
        console.info('Bubble link clicked - TODO: add some action');
      }
    },
  },
};

export default notificationMixin;
</script>
