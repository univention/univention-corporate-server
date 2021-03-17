<template>
  <div>
    <transition name="fade">
      <slot
        v-if="bubbleStateStandalone || bubbleStateNewBubble"
        name="bubble-standalone"
      />
    </transition>

    <slot
      name="bubble-embedded"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'NotificationBubble',
  computed: {
    ...mapGetters({
      bubbleState: 'notificationBubble/bubbleState',
      bubbleStateStandalone: 'notificationBubble/bubbleStateStandalone',
      bubbleStateNewBubble: 'notificationBubble/bubbleStateNewBubble',
    }),
  },
});
</script>

<style lang="stylus">
.notification-bubble
  min-width: 32rem;
  max-width: 32rem;

  &__container
    max-width: 28.8rem;
    background-color: rgba(0,0,0,0.4);
    backdrop-filter: blur(2rem);
    border-radius: var(--border-radius-notification);
    padding: 1.6rem;
    font-size: 1.6rem;
    margin-bottom: 1.6rem;

  &__standalone
    position: absolute
    right: 2rem
    top: 0.8rem
    margin: 0;

  &__embedded
    position: relative

// animation
.fade-enter-active,
.fade-leave-active
  transition: opacity .5s

.fade-enter,
.fade-leave-to
  opacity: 0
</style>
