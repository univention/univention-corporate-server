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
      <div>
        <div class="notification-bubble__header">
          <div
            class="notification-bubble__title"
          >
            {{ item.bubbleTitle }}
          </div>

          <header-button
            :aria-label="ariaLabel"
            icon="x"
            :no-click="true"
            :hover-class="`header-button__button--${item.bubbleImportance}`"
            @click.stop="dismissBubble(item.bubbleToken)"
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
import { Options, Vue } from 'vue-class-component';

import HeaderButton from '@/components/navigation/HeaderButton.vue';
import { catalog } from '@/i18n/translations';

import notificationMixin from '@/mixins/notificationMixin.vue';

@Options({
  name: 'NotificationBubbleSlot',
  components: {
    HeaderButton,
  },
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
    ariaLabel() {
      return catalog.DISMISS_NOTIFICATION.translated.value;
    },
  },
})

export default class NotificationBubbleSlot extends Vue {}
</script>

<style lang="stylus">
.notification-bubble
  &__standalone
    min-width: 32rem
    max-width: 32rem
    position: absolute
    right: 2rem
    top: 8rem
    z-index: 10

  &__embedded
    min-width: 32rem
    max-width: 32rem
    position: relative
    right: 0
    top: 0

  &__container
    max-width: 28.8rem
    backdrop-filter: blur(2rem)
    border-radius: var(--border-radius-notification)
    padding: 1.6rem
    font-size: 1.6rem
    margin-bottom: 1.6rem
    background-color: rgba(0,0,0,0.4);

    &--default
      background-color: rgba(0,0,0,0.4)

    &--success
      background-color: var(--notification-success)

    &--warning
      background-color: var(--notification-warning)

    &--error
      background-color: var(--notification-error)

  &__header
    display: flex
    align-items: center
    margin-bottom: 0.8rem

  &__title
    flex: 1 1 auto

  &__content
    padding: 0 !important
    display: block
    overflow: auto

  &__message
    text-decoration: none

    &>a
      color: #fff!important
      transition: color 250ms
      text-decoration: underline
</style>
