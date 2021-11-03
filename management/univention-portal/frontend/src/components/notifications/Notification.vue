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
  <div
    class="notification"
    :class="`notification--${importance}`"
    :data-test="`notification--${importance}`"
    @mouseenter="stopDismissal"
    @mouseleave="startDismissal"
  >
    <div class="notification__header">
      <div
        class="notification__title"
      >
        <b>
          {{ preAccouncement }}
        </b>
        <br>
        {{ title }}
      </div>
      <icon-button
        :id="`close-notification-${token}`"
        class="notification__closing-button"
        tabindex="0"
        icon="x"
        :aria-label-prop="DISMISS_NOTIFICATION"
        :data-test="`closeNotification--${importance}`"
        @click="removeNotification()"
      >
        <svg
          class="notification__closing-svg"
          viewBox="0 0 100 100"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            ref="closingCircle"
            cx="50"
            cy="50"
            r="45"
          />
        </svg>
      </icon-button>
    </div>
    <!-- eslint-disable vue/no-v-html -->
    <div
      v-if="description"
      class="notification__description"
      v-html="description"
    />
    <!-- eslint-enable vue/no-v-html -->
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';

interface NotificationData {
  dismissalTimeout: number | null,
}

export default defineComponent({
  name: 'Notification',
  components: {
    IconButton,
  },
  props: {
    title: {
      type: String,
      required: true,
    },
    description: {
      type: String,
      required: false,
      default: '',
    },
    importance: {
      type: String,
      required: true,
    },
    hidingAfter: {
      type: Number,
      required: true,
    },
    token: {
      type: Number,
      required: true,
    },
    visible: {
      type: Boolean,
      required: true,
    },
    onClick: {
      type: Function,
      required: false,
      default: null,
    },
  },
  emits: ['notificationRemoved'],
  data(): NotificationData {
    return {
      dismissalTimeout: null,
    };
  },
  computed: {
    preAccouncement(): string {
      let preAccouncement = _('Info');
      if (this.importance === 'warning') {
        preAccouncement = _('Warning');
      }
      if (this.importance === 'success') {
        preAccouncement = _('Success');
      }
      if (this.importance === 'error') {
        preAccouncement = _('Error');
      }
      return `${preAccouncement}:`;
    },
    DISMISS_NOTIFICATION(): string {
      return `${_('Dismiss notification')}: ${this.title}`;
    },
  },
  mounted() {
    this.startDismissal();
  },
  beforeUnmount() {
    this.stopDismissal();
  },
  methods: {
    startDismissal() {
      if (this.hidingAfter < 0) {
        return;
      }
      if (this.hidingAfter === 0) {
        this.hideNotification();
        return;
      }
      setTimeout(() => {
        this.$el.style = `--closing-duration: ${this.hidingAfter}s;`;
        this.$el.classList.add('notification__dismissing');
        this.dismissalTimeout = setTimeout(() => this.hideNotification(),
          this.hidingAfter * 1000);
      }, 50); // $nextTick is still too soon
    },
    stopDismissal() {
      if (this.dismissalTimeout) {
        clearTimeout(this.dismissalTimeout);
        this.$el.style = '--closing-duration: 0s;';
        this.$el.classList.remove('notification__dismissing');
      }
    },
    removeNotification() {
      // this.$emit('notificationRemovedBefore');
      this.$store.dispatch('notifications/removeNotification', this.token);
      this.$emit('notificationRemoved');
    },
    hideNotification() {
      this.$store.dispatch('notifications/hideNotification', this.token);
    },
  },
});

</script>

<style lang="stylus">
.flyout-wrapper
  .notification__closing-svg
    display: none

.notification
  border-radius: var(--border-radius-notification)
  margin-bottom: calc(2 * var(--layout-spacing-unit))
  padding: var(--layout-spacing-unit)
  padding-bottom: var(--layout-spacing-unit)
  padding-left: calc(3 * var(--layout-spacing-unit))

  &.notification__dismissing
    .notification__closing-svg circle
      stroke-dashoffset: 283
      transition: stroke-dashoffset linear var(--closing-duration)

  &__closing-button:hover, &__closing-button:focus
    .notification__closing-svg
      display: none

  &__closing-svg
    position: absolute
    top: -2px
    left: -2px
    right: -2px
    bottom: -2px
    pointer-events: none

    circle
      display: block
      fill: transparent
      stroke: var(--color-focus)
      stroke-linecap: round
      stroke-dasharray: 283
      stroke-dashoffset: 0
      stroke-width: 0.2rem
      transform-origin: 50% 50%
      transform: scale(1, -1) rotate(90deg)

  .icon-button
    border: 0.1rem solid transparent
    align-self: flex-start;

    &:hover, &:focus, &:active
      background-color: transparent
      border-color: var(--color-focus)

  &--default
    background-color: var(--bgc-popup)

  &--success
    background-color: var(--bgc-success)

  &--warning
    background-color: var(--bgc-warning)

  &--error
    background-color: var(--bgc-error)

  &__header
    display: flex
    align-items: center

  &__title
    flex: 1 1 auto

  &__description
    padding: 0 !important
    overflow: auto
    margin-top: var(--layout-spacing-unit)
    padding-right: calc(2 * var(--layout-spacing-unit))

    &>a
      color: var(--color-white) !important
      transition: color var(--portal-transition-duration)
      text-decoration: underline

    ul
      padding-left: calc(2* var(--layout-spacing-unit))
      margin-top: 0

  svg
    margin-right: 0!important
</style>
