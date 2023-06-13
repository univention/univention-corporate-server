<template>
  <div
    v-if="visible"
    :class="[
      'announcement',
      `announcement--${severity}`,
      {
        'announcement--sticky': sticky
      }
    ]"
    role="alert"
  >
    <div class="announcement__content">
      <h4 class="announcement__title">
        {{ $localized(title) }}
      </h4>
      <p
        v-if="message"
        class="announcement__message"
      >
        {{ $localized(message) }}
      </p>
    </div>
    <div class="announcement__closeWrapper">
      <icon-button
        icon="x"
        :aria-label-prop="CLOSE"
        @click="onCloseClick"
      />
    </div>
  </div>
</template>

<script lang="ts">
import { LocalizedString, PortalAnnouncementSeverity } from '@/store/modules/portalData/portalData.models';
import { defineComponent, PropType } from 'vue';
import IconButton from '@/components/globals/IconButton.vue';
import _ from '@/jsHelper/translate';

export default defineComponent({
  name: 'Announcement',
  components: {
    IconButton,
  },
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
  computed: {
    CLOSE(): string {
      return _('Close');
    },
  },
  methods: {
    getAnnouncementVisibility(): boolean {
      const visibility = localStorage.getItem(`${this.name}_visible`);
      if (visibility) {
        return JSON.parse(visibility);
      }
      return true;
    },
    onCloseClick() {
      this.visible = false;
      localStorage.setItem(`${this.name}_visible`, JSON.stringify(false));
    },
  },
});
</script>

<style lang="stylus">
.announcement
  display: flex
  background-color: var(--bgc-content-container)
  &--info
    background-color: var(--bgc-announcements-info)

  &--danger
    background-color: var(--bgc-announcements-danger)

  &--success
    background-color: var(--bgc-announcements-success)

  &--warn
    background-color: var(--bgc-announcements-warn)

.announcement__content
  text-align: center
  flex: 1 1 auto

.announcement__title,
.announcement__message
  margin: calc(2 * var(--layout-spacing-unit)) var(--layout-spacing-unit)

.announcement__closeWrapper
  padding: var(--layout-spacing-unit)

.announcement--sticky .announcement__closeWrapper
  display: none
</style>
