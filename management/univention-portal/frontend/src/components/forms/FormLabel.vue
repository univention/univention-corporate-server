<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <label
    :for="forAttr"
    class="form-label"
  >
    {{ label }}
    <span
      v-if="required"
      aria-hidden="true"
    >*</span>
    <button
      v-if="showHelpIcon"
      type="button"
      class="form-label__button"
      :tabindex="tabindex"
      @click="toggleHelpText"
    >
      <span class="sr-only sr-only-mobile">{{ HELP_TEXT }}</span>
      <portal-icon
        :icon="icon"
        class="form-label__portal-icon"
      />
    </button>
  </label>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';
import PortalIcon from '@/components/globals/PortalIcon.vue';

export default defineComponent({
  name: 'Label',
  components: {
    PortalIcon,
  },
  props: {
    forAttr: {
      type: String,
      required: true,
    },
    label: {
      type: String,
      required: true,
    },
    required: {
      type: Boolean,
      default: false,
    },
    invalidMessage: {
      type: String,
      default: '',
    },
    showHelpIcon: {
      type: Boolean,
      default: false,
    },
    displayDescription: {
      type: Boolean,
      default: false,
    },
    tabindex: {
      type: Number,
      default: 0,
    },
  },
  emits: ['toggleDescription'],
  computed: {
    HELP_TEXT(): string {
      return `${this.label}: ${this.buttonText}`;
    },
    icon(): string {
      return this.displayDescription ? 'x-circle' : 'help-circle';
    },
    buttonText(): string {
      return this.displayDescription ? _('Hide Description') : _('Show Description');
    },
  },
  methods: {
    toggleHelpText(): void{
      this.$emit('toggleDescription');
    },
  },
});
</script>

<style lang="stylus">
.form-label
  display: flex
  align-items: center
  padding-bottom: 0.2rem;

  &__button
    padding: unset
    background-color: unset
    border-radius: 100rem
    width: 1.5rem
    height: 1.5rem
    border-width: 0.1rem
    margin-left:0.2rem

  &__portal-icon
    color: var(--font-color-contrast-middle);
    width: 0.8rem
    margin-left: 0
    margin-right: 0 !important

</style>
