<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div
    v-if="visible"
    :class="[
      'announcement',
      `announcement--${severity}`,
      {
        'announcement--withMessage': hasMessage,
        'announcement--sticky': sticky
      }
    ]"
    role="alert"
  >
    <h4 class="announcement__title">
      {{ $localized(title) }}
    </h4>
    <div class="announcement__closeWrapper">
      <icon-button
        icon="x"
        class="announcement__closeButton"
        :aria-label-prop="CLOSE"
        @click="onCloseClick"
      />
    </div>
    <p
      v-if="hasMessage"
      class="announcement__message"
    >
      {{ $localized(message) }}
    </p>
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
      default: () => ({}),
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
    hasMessage(): boolean {
      // TODO FIXME
      // univention.udm.encoders.ListOfListOflTextToDictPropertyEncoder.decode([])
      // returns `[]` instead of `{}` so this is a workaround for that.
      if (Array.isArray(this.message)) {
        return false;
      }
      return Object.keys(this.message).length > 0;
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
  display: grid
  grid-template-columns: 1fr auto
  border-radius: var(--border-radius-container)
  background-color: var(--bgc-content-container)
  min-height calc(8 * var(--layout-spacing-unit))

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

.announcement__title
  margin: 0
  padding: var(--layout-spacing-unit)
  display: flex
  justify-content: center
  align-items: center

.announcement__message
  margin: 0
  padding: var(--layout-spacing-unit)
  text-align: center

.announcement__closeWrapper
  padding: var(--layout-spacing-unit)
  display: flex
  align-items: center

.announcement--sticky .announcement__closeButton
  visibility: hidden

.announcement.announcement--withMessage
  .announcement__title,
  .announcement__closeWrapper
    border-bottom: 1px solid var(--bgc-content-body)
</style>
