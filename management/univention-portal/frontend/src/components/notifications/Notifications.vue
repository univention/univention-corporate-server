<!--
Copyright 2021 Univention GmbH

https://www.univention.de/

All rights reserved.

The source code of this program is made available
under the terms of the GNU Affero General Public License version 3
(GNU AGPL V3) as published by the Free Software Foundation.

Binary versions of this program provided by Univention to you as
well as other copyrighted, protected or trademarked materials like
Logos, graphics, fonts, specific documentations and configurations,
cryptographic keys etc. are subject to a license agreement between
you and Univention and not subject to the GNU AGPL V3.

In the case you use this program under the terms of the GNU AGPL V3,
the program is provided in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License with the Debian GNU/Linux or Univention distribution in file
/usr/share/common-licenses/AGPL-3; if not, see
<https://www.gnu.org/licenses/>.
-->
<template>
  <region
    :id="`notifications-${onlyVisible ? 'visible' : 'all'}`"
    direction="topdown"
    class="notifications"
    @keydown.esc="closeNotifications"
  >
    <notification
      v-for="notification in notifications"
      :key="notification.token"
      v-bind="notification"
    />
  </region>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import Region from '@/components/activity/Region.vue';
import Notification from '@/components/notifications/Notification.vue';

export default defineComponent({
  name: 'Notifications',
  components: {
    Notification,
    Region,
  },
  props: {
    onlyVisible: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      allNotifications: 'notifications/allNotifications',
      visibleNotifications: 'notifications/visibleNotifications',
      activeButton: 'navigation/getActiveButton',
    }),
    notifications() {
      if (this.onlyVisible) {
        return this.visibleNotifications;
      }
      return this.allNotifications;
    },
  },
  methods: {
    closeNotifications(): void {
      if (this.activeButton === 'bell') {
        this.$store.dispatch('navigation/setActiveButton', '');
      }
    },
  },
});

</script>

<style lang="stylus">
.notifications
  position: fixed
  z-index: $zindex-4
  top: calc(var(--layout-height-header) + 1rem)
  right: var(--layout-spacing-unit)
  width: 90vw
  max-width: 300px
  max-height: 100%
  overflow-y: auto
  padding-right: calc(3 * var(--layout-spacing-unit))
</style>
