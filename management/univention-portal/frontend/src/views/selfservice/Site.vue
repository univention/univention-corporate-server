<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <modal-wrapper
    :is-active="initialLoadDone"
    :full="true"
    class="modal-wrapper--selfservice"
  >
    <modal-dialog
      ref="dialog"
      :i18n-title-key="title"
      modal-level="selfservice"
      class="dialog--selfservice"
      @cancel="cancel"
    >
      <template
        v-if="subtitle"
        #description
      >
        {{ subtitle }}
      </template>
      <slot />
    </modal-dialog>
  </modal-wrapper>
</template>

<script lang="ts">
// FIXME if using 'initialLoadDone' for is-active there are weird z-indexing css issues with the opacity animation
import { defineComponent } from 'vue';

import ModalWrapper from '@/components/modal/ModalWrapper.vue';
import ModalDialog from '@/components/modal/ModalDialog.vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'Site',
  components: {
    ModalDialog,
    ModalWrapper,
  },
  props: {
    title: {
      type: String,
      required: true,
    },
    subtitle: {
      type: String,
      default: '',
    },
  },
  computed: {
    ...mapGetters({
      initialLoadDone: 'getInitialLoadDone',
    }),
  },
  mounted() {
    this.$store.dispatch('activity/setLevel', 'selfservice');
    document.body.classList.add('body--has-selfservice');
  },
  unmounted() {
    this.$store.dispatch('activity/setLevel', 'portal');
    document.body.classList.remove('body--has-selfservice');
  },
  methods: {
    cancel() {
      this.$router.push({ name: 'portal' });
    },
  },
});
</script>

<style lang="stylus">
body.body--has-selfservice
  overflow: hidden

.modal-wrapper--selfservice
  padding: calc(4 * var(--layout-spacing-unit)) 0
  overflow: auto
  box-sizing: border-box
  &.modal-wrapper--isVisible
    // z-index: $zindex-4 TODO notifications are also $zindex-4
    z-index: 399

.dialog--selfservice
  margin: auto
  box-sizing: border-box
  min-width: s('min(calc(var(--inputfield-width) + calc(12 * var(--layout-spacing-unit))), 90%)')
  min-height: s('min(200px, 90%)')
  max-height: unset

  input,
  select,
  form
    width: 100%

  form main
    max-height: unset
    padding: 0
</style>
