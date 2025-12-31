<!--
SPDX-FileCopyrightText: 2021-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <section
    :class="[
      'dialog',
      {'dialog--unfocusable': !isFocusable}
    ]
    "
    role="dialog"
    aria-modal="true"
    :aria-labelledby="labelledbyId"
    :aria-describedby="describedbyId"
    @keydown.esc="cancel()"
  >
    <header
      class="dialog__header"
    >
      <h3 :id="labelledbyId">
        <span v-if="i18nTitleKey">
          {{ I18N_TITLE_KEY }}
        </span>
        <span v-else>
          {{ title }}
        </span>
      </h3>
      <icon-button
        v-if="cancelAllowed"
        icon="x"
        class="button--flat"
        :aria-label-prop="CANCEL"
        :active-at="[modalLevel]"
        @click="cancel()"
      />
    </header>
    <div
      :id="describedbyId"
    >
      <slot name="description" />
    </div>
    <slot />
  </section>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'ModalDialog',
  components: {
    IconButton,
  },
  props: {
    i18nTitleKey: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: '',
    },
    modalLevel: {
      type: String,
      default: 'modal', // pass 'modal2' if modal is in second Level
    },
    cancelAllowed: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  emits: ['cancel'],
  computed: {
    ...mapGetters({
      getModalState: 'modal/getModalState',
    }),
    I18N_TITLE_KEY(): string {
      return _('%(key1)s', { key1: this.i18nTitleKey });
    },
    CANCEL(): string {
      return _('Cancel');
    },
    labelledbyId(): string {
      return `${this.$.uid}-labelledby`;
    },
    describedbyId(): string {
      return `${this.$.uid}-describedby`;
    },
    isFocusable(): boolean {
      return !this.getModalState('secondLevelModal');
    },
  },
  methods: {
    cancel(): void {
      if (this.cancelAllowed) {
        this.$emit('cancel');
      }
    },
  },
});
</script>

<style lang="stylus">
.dialog
  padding: calc(2 * var(--layout-spacing-unit)) calc(4 * var(--layout-spacing-unit))
  background: var(--bgc-content-container)
  border-radius: var(--border-radius-container)
  max-width: calc(50 * var(--layout-spacing-unit))
  box-shadow: var(--box-shadow)

  @media $mqSmartphone
    max-width: calc(100% - 8 * var(--layout-spacing-unit))
    padding: calc(2 * var(--layout-spacing-unit)) calc(2 * var(--layout-spacing-unit))
    --local-sticky-top: calc(var(--layout-height-header) + var(--layout-spacing-unit))
    --local-sticky-bottom: var(--layout-spacing-unit)
    max-height: calc(100vh - (var(--local-sticky-top) + var(--local-sticky-bottom)))
    overflow: auto
    overflow-x: hidden
    position: sticky !important
    top: var(--local-sticky-top)
    bottom: var(--local-sticky-bottom)
    box-sizing: border-box

  form
    width: calc(var(--inputfield-width) + 3rem)

    @media $mqSmartphone
      max-width: 100%

  main
    max-height: 26rem
    overflow: auto
    padding-right: var(--layout-spacing-unit)

    > label:first-child
      margin-top: 0

    @media $mqSmartphone
      max-height: none
      overflow: unset
  &--unfocusable
    main
      overflow: hidden
  footer:not(.image-upload__footer):not(.multi-select__footer)
    margin-top: calc(2 * var(--layout-spacing-unit))
    padding-top: calc(2 * var(--layout-spacing-unit))
    border-top: thin solid var(--bgc-tab-separator)
    /* padding: var(--layout-spacing-unit-small) calc(2 * var(--layout-spacing-unit))*/
    display: flex
    justify-content: space-between
    flex-wrap: wrap

    button:last-of-type
      margin-left: auto

  &__header
    display: flex
    align-items: center

    @media $mqSmartphone
      position: sticky;
      top: 0;
      z-index: 9;
      background-color: var(--bgc-content-container)

      &:before
        content: ''
        width: 100%
        height: calc(2 * var(--layout-spacing-unit))
        top: calc(-2 * var(--layout-spacing-unit))
        position: absolute
        background-color: var(--bgc-content-container)

    button
      margin-left: auto
</style>
