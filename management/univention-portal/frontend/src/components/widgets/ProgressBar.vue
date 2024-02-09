<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div class="progress-bar">
    <div
      :id="randomId"
      class="progress-bar__title"
    >
      {{ title }}
    </div>

    <div
      class="progress-bar__line"
      role="progressbar"
      :aria-labelledby="randomId"
      :aria-valuenow="isIndeterminate ? null : value"
    >
      <Transition
        appear
        name="fade"
      >
        <div
          v-if="isIndeterminate"
          class="progress-bar__line--empty"
          role="presentation"
        />
        <div
          v-else-if="!isIndeterminate"
          class="progress-bar__percent"
          role="presentation"
          :style="{ width: `${current}%`}"
        />
      </Transition>
    </div>
    <div class="progress-bar__message">
      <span
        class="progress-bar__message__text"
      >{{ message }}</span>
      <span
        v-if="!isIndeterminate"
        class="progress-bar__message__percent"
      >{{ valueString }}</span>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { randomId } from '@/jsHelper/tools';

export default defineComponent({
  name: 'ProgressBar',
  props: {
    percentage: {
      type: Number,
      required: true,
    },
    title: {
      type: String,
      required: true,
    },
    message: {
      type: String,
      default: '',
    },
  },
  data: () => ({
    min: 0,
    max: 100,
    current: 0,
    randomId: `progress-bar-${randomId()}`,
  }),
  computed: {
    /**
     * clamp to min, max and cover isNaN value
     */
    value(): number {
      const clamp = (num, min, max) => Math.min(Math.max(num, min), max);
      const value = clamp(this.percentage, this.min, this.max);
      return Number.isNaN(value) ? this.min : value;
    },
    isIndeterminate(): boolean {
      return this.percentage < this.min;
    },
    valueString(): string {
      return `${this.value}%`;
    },
  },
  watch: {
    percentage(value, oldValue) {
      if (value !== oldValue) {
        this.current = this.value;
      }
    },
  },
  mounted() {
    setTimeout(() => {
      this.current = this.value;
    }, 0);
  },
});
</script>

<style lang="stylus">
@keyframes loop {
  0% { background-position-x: 0 }
  100% { background-position-x: -2rem }
}

.progress-bar
  width: auto
  padding: calc(2 * var(--layout-spacing-unit))
  border-radius: var(--border-radius-container)
  color: var(--font-color-contrast-high)
  background-color: var(--bgc-content-container)

  &__title
    min-height: calc(2 * 1em * var(--font-lineheight-normal))
    font-size: var(--font-size-2)
    font-weight: var(--font-weight-bold)
    margin-bottom: calc(2 * var(--layout-spacing-unit))
    overflow: hidden
    overflow-wrap: break-word

  &__line
    border: none
    background-color: var(--bgc-progressbar-empty)
    height: 0.5rem
    position: relative
    top: 0

    &--empty
      position: absolute
      left: 0
      top: 0
      width: 100%
      height: 100%
      background-size: 1rem 1rem;
      background-image: linear-gradient(
        135deg,
        var(--font-color-contrast-low) 25%,
        transparent 25%,
        transparent 50%,
        var(--font-color-contrast-low) 50%,
        var(--font-color-contrast-low) 75%,
        transparent 75%,
        transparent
      );
      animation: loop 1.5s infinite linear

  &__percent
    border: none
    background-color: var(--button-primary-bgc)
    height: 100%
    transition: all 1s;
    position: absolute
    left: 0
    top: 0

  &__message
    display: grid
    grid-template-columns: auto 4ch
    gap: 0 var(--layout-spacing-unit-small)
    margin-top: calc(2 * var(--layout-spacing-unit))

    &__text
      min-height: calc(3 * 1em * var(--font-lineheight-normal))
      font-size: var(--font-size-4)
      color: var(--font-color-contrast-middle)
      overflow: hidden
      overflow-wrap: break-word

    &__percent
      color: var(--font-color-contrast-middle)
      font-size: var(--font-size-4)
      justify-self: flex-end

// <transition fade
.fade-enter-active, .fade-leave-active
  transition: all 1s

.fade-enter-from, .fade-leave-to
  opacity: 0
</style>
