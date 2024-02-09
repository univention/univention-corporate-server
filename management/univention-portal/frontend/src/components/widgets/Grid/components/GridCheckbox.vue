<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div
    class="checkbox"
    aria-disabled="false"
    :aria-checked="checked"
    :aria-label="isHeader ? 'Select all' : 'Select row'"
    role="checkbox"
    tabindex="0"
    @click="onCheck"
    @keydown="onKeydownCheck"
  >
    <Transition>
      <PortalIcon
        v-if="checked === true"
        icon="check"
        role="presentation"
        :style="[{ marginBottom: isHeader && '6px' }]"
      />
    </Transition>
    <Transition>
      <PortalIcon
        v-if="isHeader && checked === 'mixed'"
        icon="minus"
        role="presentation"
        style="margin-bottom: 8px"
      />
    </Transition>
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import { HeaderCheckboxState } from '../types';

export default defineComponent({
  name: 'GridCheckbox',
  components: {
    PortalIcon,
  },
  props: {
    checked: {
      type: [Boolean, String] as PropType<HeaderCheckboxState>,
      required: true,
    },
    isHeader: {
      type: Boolean as PropType<boolean>,
      default: false,
    },
  },
  emits: ['update:checked'],
  methods: {
    onCheck() {
      if (!this.isHeader) {
        this.$emit('update:checked', !this.checked);
      } else {
        let checked = false;
        if (this.checked === false) checked = true;
        // if this.checked is true or mixed, then set to false (already set)
        this.$emit('update:checked', checked);
      }
    },
    onKeydownCheck({ keyCode }) {
      const spaceBarKeyCode = 32;
      if (keyCode && keyCode === spaceBarKeyCode) {
        this.onCheck();
      }
    },
  },
});
</script>

<style lang="stylus">
.checkbox
  --local-border-color: var(--font-color-contrast-low)
  --local-background-color: transparent
  width: var(--font-size-4)
  height: var(--font-size-4)
  background-color: var(--local-background-color)
  transition: all 250ms ease-in-out
  margin-right: var(--layout-spacing-unit-small)
  border: 2px solid
  border-radius: 2px

  &:hover
    background-color: var(--bgc-checkbox-hover)

  &[aria-checked=false]
    border-color: var(--local-border-color)

  &[aria-checked=true], &[aria-checked=mixed]
    border-color: var(--color-accent)

  & svg
    height: 15px
    width: 15px
    color: var(--color-accent)
</style>
