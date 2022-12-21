<template>
  <div
    v-show="visible"
    :class="['announcement', `announcement--${severity}`]"
    role="alert"
  >
    <div class="content">
      <h4 class="announcement-title">
        {{ $localized(title) }}
      </h4>
      <p
        v-if="message"
        class="announcement-message"
      >
        {{ $localized(message) }}
      </p>
      <slot />
    </div>
    <a
      v-if="!sticky"
      href="#"
      class="close-link"
      @click.prevent="onCloseClick"
    >
      X
    </a>
  </div>
</template>

<script lang="ts">
import { LocalizedString, PortalAnnouncementSeverity } from '@/store/modules/portalData/portalData.models';
import { defineComponent, PropType } from 'vue';

export default defineComponent({
  name: 'Announcement',
  props: {
    name: {
      type: String,
      required: true,
    },
    title: {
      type: Object as PropType<LocalizedString>,
      required: true,
    },
    message: {
      type: Object as PropType<LocalizedString>,
      default: '',
    },
    severity: {
      type: String as PropType<PortalAnnouncementSeverity>,
      default: 'success',
    },
    sticky: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      visible: this.getAnnouncementVisibility(),
    };
  },
  methods: {
    setAnnouncementVisibility(visibility: boolean): void {
      this.visible = false;
      localStorage.setItem(`${this.name}_visible`, JSON.stringify(visibility));
    },
    getAnnouncementVisibility(): boolean {
      const visibility = localStorage.getItem(`${this.name}_visible`);
      if (visibility) {
        return JSON.parse(visibility);
      }
      return true;
    },
    onCloseClick() {
      this.setAnnouncementVisibility(false);
    },
  },
});

</script>

<style lang="stylus" scoped>
.announcement
  display: grid
  grid-template-columns: 1fr auto
  gap: 2rem
  justify-content: center
  background-color: var(--serveroverview-tile-hover-color)
  color: white
  min-height: 2rem

  .content
    text-align: center

  .announcement-title
    margin-right: .5rem

  .close-link
    padding: .4rem
    font-size: 1.2rem
    color: #fff
    text-decoration: none

  .close-link
    padding: .4rem
    font-size: 1.2rem
    color: #fff
    text-decoration: none

  .announcement-message
    margin-right: .5rem

  .announcement-close
    margin-left: .5rem

  &--info
    background-color: var(--color-accent)

  &--danger
    background-color: var(--bgc-error)

  &--success
    background-color: var(--bgc-success)

  &--warn
    background-color: var(--bgc-warning)

</style>
