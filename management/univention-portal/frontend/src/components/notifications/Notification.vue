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
        tabindex="0"
        icon="x"
        :aria-label-prop="ariaLabelDismissNotification"
        @click="dismissNotification()"
      />
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
  data(): NotificationData {
    return {
      dismissalTimeout: null,
    };
  },
  computed: {
    ariaLabelDismissNotification(): string {
      return this.$translateLabel('DISMISS_NOTIFICATION');
    },
    preAccouncement(): string {
      let preAccouncement = this.$translateLabel('DEFAULT_NOTIFICATION');
      if (this.importance === 'warning') {
        preAccouncement = this.$translateLabel('WARNING');
      }
      if (this.importance === 'success') {
        preAccouncement = this.$translateLabel('SUCCESS');
      }
      if (this.importance === 'error') {
        preAccouncement = this.$translateLabel('ERROR');
      }
      return `${preAccouncement}:`;
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
        this.dismissNotification();
        return;
      }
      setTimeout(() => {
        this.$el.style = `transition-duration: ${this.hidingAfter}s;`;
        this.$el.classList.add('notification__dismissing');
        this.dismissalTimeout = setTimeout(() => this.dismissNotification(),
          this.hidingAfter * 1000);
      }, 50); // $nextTick is still too soon
    },
    stopDismissal() {
      if (this.dismissalTimeout) {
        clearTimeout(this.dismissalTimeout);
        this.$el.style = 'transition-duration: 0s;';
        this.$el.classList.remove('notification__dismissing');
      }
    },
    dismissNotification() {
      this.$store.dispatch('notifications/removeNotification', this.token);
    },
  },
});

</script>

<style lang="stylus">
.notification
  border-radius: var(--border-radius-notification)
  margin-bottom: calc(2 * var(--layout-spacing-unit))
  padding: var(--layout-spacing-unit)
  padding-bottom: var(--layout-spacing-unit)
  padding-left: calc(3 * var(--layout-spacing-unit))
  transition: background 0s ease-out
  background: linear-gradient(to right, rgba(0, 0, 0, 0.3) 50%, rgba(0, 0, 0, 0.1) 50%);
  background-size: 200% 100%;
  background-position: left bottom;

  &.notification__dismissing
    background-position: right bottom

  .icon-button
    border: 0.1rem solid transparent

    &:hover, &:focus, &:active
      background-color: transparent
      border-color: var(--color-focus)

  &--default
    background-color: rgba(0, 0, 0, 0.6)

  &--success
    background-color: var(--color-notification-success)

  &--warning
    background-color: var(--color-notification-warning)

  &--error
    background-color: var(--notification-error)

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
</style>
