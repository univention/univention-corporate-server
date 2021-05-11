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
    :class="`notification-bubble__${bubbleContainer}`"
  >
    <div
      v-for="(item, index) in setBubbleContent"
      :key="index"
      class="notification-bubble__container"
      :class="`notification-bubble__container--${item.bubbleImportance}`"
    >
      <div
        :class="{'notification-bubble__clickable': clickable(item)}"
        @click="onClick(item)"
      >
        <div class="notification-bubble__header">
          <div
            class="notification-bubble__title"
          >
            {{ item.bubbleTitle }}
          </div>

          <header-button
            :aria-label="ariaLabelDismissButton"
            icon="x"
            :no-click="true"
            :hover-class="`header-button__button--${item.bubbleImportance}`"
            @click.stop="dismissNotification(item.bubbleToken)"
          />
        </div>

        <div class="notification-bubble__content">
          <!-- eslint-disable vue/no-v-html -->
          <div
            v-if="item && item.bubbleDescription"
            class="notification-bubble__message"
            v-html="item.bubbleDescription"
          />
          <!-- eslint-enable vue/no-v-html -->
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import HeaderButton from '@/components/navigation/HeaderButton.vue';
import notificationMixin from '@/mixins/notificationMixin.vue';

import { catalog } from '@/i18n/translations';

export default defineComponent({
  name: 'NotificationBubbleSlot',
  components: { HeaderButton },
  mixins: [
    notificationMixin,
  ],
  props: {
    bubbleContainer: {
      type: String,
      default: 'standalone',
    },
  },
  computed: {
    setBubbleContent() {
      let data;
      if (this.bubbleStateNewBubble && this.bubbleContainer === 'standalone') {
        data = this.bubbleContentNewNotification;
      } else if (this.bubbleContainer === 'embedded') {
        data = this.bubbleContent;
      }
      return data;
    },
    ariaLabelDismissButton() {
      return catalog.DISMISS_NOTIFICATION.translated.value;
    },
  },
  methods: {
    clickable(item): boolean {
      return !!item.onClick;
    },
    onClick(item): void {
      if (this.clickable(item)) {
        item.onClick();
      }
    },
  },
});

</script>

<style lang="stylus">
.notification-bubble
  &__standalone
    position: absolute
    right: 2rem
    top: 8rem
    z-index: 10

  &__clickable
    cursor: pointer

  &__embedded
    position: relative
    right: 0
    top: 0

  &__container
    backdrop-filter: blur(2rem)
    border-radius: var(--border-radius-notification)
    padding: var(--layout-spacing-unit)
    padding-left: calc(3 * var(--layout-spacing-unit))
    margin-bottom: calc(2 * var(--layout-spacing-unit))
    background-color: rgba(0, 0, 0, 0.4)

    &--default
      background-color: rgba(0,0,0,0.4)

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

  &__content
    padding: 0 !important
    display: block
    overflow: auto

  &__message
    margin-top: var(--layout-spacing-unit)
    text-decoration: none
    padding-right: calc(2 * var(--layout-spacing-unit))

    &>a
      color: var(--color-white)!important
      transition: color 250ms
      text-decoration: underline
</style>
