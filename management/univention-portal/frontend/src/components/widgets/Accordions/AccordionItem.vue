<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div class="accordion-item">
    <div
      class="accordion-item-header"
      @click="toggleExpanded"
    >
      <slot
        name="header"
      >
        <div class="accordion-item-header-default">
          <h2 class="accordion-item-header-default__title">
            {{ title }}
          </h2>
          <IconButton
            class="accordion-item-header-default__expanded-button"
            :class="{
              'accordion-item-header-default__expanded-button--expanded': isExpanded,
            }"
            aria-label-prop="Expand"
            icon="chevron-down"
            @click="toggleExpanded"
          />
        </div>
      </slot>
    </div>
  </div>
  <Transition
    name="expand"
    @before-enter="beforeEnter"
    @enter="enter"
    @before-leave="beforeLeave"
    @leave="leave"
  >
    <div
      v-show="isExpanded"
      ref="body"
      class="accordion-item-body"
    >
      <slot />
    </div>
  </Transition>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'AccordionItem',
  components: { IconButton },
  props: {
    title: {
      type: String,
      default: '',
    },
  },
  data() {
    return {
      isExpanded: false,
      itemBodyHeight: 0,
    };
  },
  methods: {
    toggleExpanded() {
      this.isExpanded = !this.isExpanded;
    },
    // Transition hooks
    beforeEnter(el) {
      el.style.height = '0';
    },
    enter(el) {
      el.style.height = `${el.scrollHeight}px`;
    },
    beforeLeave(el) {
      el.style.height = `${el.scrollHeight}px`;
    },
    leave(el) {
      el.style.height = '0';
    },
  },
});
</script>

<style lang="stylus">

.accordion-item
  @media (prefers-color-scheme: dark) {
    --bgc-titlepane-hover: rgba(255,255,255,0.04)
  }
  @media (prefers-color-scheme: light) {
    --bgc-titlepane-hover: rgba(0, 0, 0, 0.04)
  }
  border-top: 2px solid var(--bgc-content-body)
  margin-bottom: 0

  &-header
    &-default
      display: flex
      align-items: center
      justify-content: space-between
      transition: background-color 0.2s
      padding: var(--layout-spacing-unit)

      &:hover
        background-color: var(--bgc-titlepane-hover)
        cursor: pointer

      &__title
        font-size: var(--font-size-2)
        line-height: var(--font-lineheight-normal)
        font-weight: 600

      &__expanded-button
        transition: transform 0.5s
        &--expanded
          transform: rotate(180deg)

  &-body
    padding: var(--layout-spacing-unit)
    transition: 0.15s ease-out
    overflow: hidden;

</style>
