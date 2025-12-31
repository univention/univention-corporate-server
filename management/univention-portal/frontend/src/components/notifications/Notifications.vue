<!--
SPDX-FileCopyrightText: 2021-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <region
    :id="`notifications-${!isInNotificationBar ? 'visible' : 'all'}`"
    ref="region"
    :aria-live="ariaLiveStatus"
    direction="topdown"
    :class="['notifications',
             {
               'notifications--in-bar' : isInNotificationBar,
               'notifications--floating' : !isInNotificationBar,
             }]"
    @keydown.esc="closeNotificationsSidebar"
  >
    <div
      v-if="isInNotificationBar && notifications.length > 1"
      class="notifications__close-all"
    >
      <button
        ref="removeAllNotificationsButton"
        type="button"
        @click.prevent="removeAllNotifications"
      >
        <portal-icon
          icon="trash"
        />
        <span>
          {{ REMOVE_ALL_NOTIFICATIONS }}
        </span>
      </button>
    </div>
    <notification
      v-for="notification in notifications"
      :key="notification.token"
      v-bind="notification"
      @notificationRemoved="onNotificationRemoved"
    />
    <span
      v-if="isInNotificationBar && notifications.length === 0"
      class="notifications__no-notifications"
    >
      {{ NO_NOTIFICATIONS }}
    </span>
  </region>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import Region from '@/components/activity/Region.vue';
import Notification from '@/components/notifications/Notification.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';

export default defineComponent({
  name: 'Notifications',
  components: {
    Notification,
    Region,
    PortalIcon,
  },
  props: {
    isInNotificationBar: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    ...mapGetters({
      allNotifications: 'notifications/allNotifications',
      visibleNotifications: 'notifications/visibleNotifications',
      numNotifications: 'notifications/numNotifications',
    }),
    notifications() {
      if (!this.isInNotificationBar) {
        return this.visibleNotifications;
      }
      return this.allNotifications;
    },
    REMOVE_ALL_NOTIFICATIONS(): string {
      return _('Remove all');
    },
    NO_NOTIFICATIONS(): string {
      return _('No notifications');
    },
    NOTIFICATIONS_REMOVED(): string {
      return _('Notifications removed');
    },
    NOTIFICATION_REMOVED(): string {
      return _('Notification removed');
    },
    ariaLiveStatus(): string {
      return !this.isInNotificationBar ? 'polite' : 'off';
    },
  },
  created() {
    if (this.isInNotificationBar) {
      this.$store.dispatch('modal/disableBodyScrolling');
    }
  },
  mounted(): void {
    if (this.isInNotificationBar && this.notifications.length > 1) {
      (this.$refs.removeAllNotificationsButton as HTMLElement).focus();
    } else {
      this.$store.dispatch('activity/setRegion', 'notifications-all');
    }
  },
  methods: {
    removeAllNotifications(): void {
      this.$store.dispatch('notifications/removeAllNotifications');
      this.$store.dispatch('activity/setMessage', _('Notifications removed'));
      this.closeNotificationsSidebar();
    },
    closeNotificationsSidebar(): void {
      this.$store.dispatch('navigation/closeNotificationsSidebar');
    },
    onNotificationRemoved() {
      this.$store.dispatch('activity/setMessage', _('Notification removed'));
      if (this.numNotifications === 0) {
        this.closeNotificationsSidebar();
      } else {
        // @ts-ignore
        this.$refs.region.goUp();
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

  @media $mqSmartphone
    font-size: var(--font-size-5)
    width: 73vw
    padding-right: 0

  &--in-bar
    @media $mqSmartphone
      right: 0
      left: calc(3 * var(--layout-spacing-unit))
      font-size: var(--font-size-5)

  &--floating
    @media $mqSmartphone
      right: var(--layout-spacing-unit)

  &__close-all
    display: flex
    justify-content: flex-start
    margin-bottom: calc(4 * var(--layout-spacing-unit))

  &__no-notifications
    font-size: var(--font-size-2)

  .flyout-wrapper &
    top: calc(4 * var(--layout-spacing-unit));
    bottom: 0
</style>
