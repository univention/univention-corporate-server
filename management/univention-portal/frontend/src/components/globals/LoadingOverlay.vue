<!--
SPDX-FileCopyrightText: 2021-2026 Univention GmbH
SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <modal-wrapper
    :is-active="loadingState"
    :modal-level="2"
    class="modal-wrapper--loading"
  >
    <standby-wrapper />
  </modal-wrapper>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import ModalWrapper from '@/components/modal/ModalWrapper.vue';
import StandbyWrapper from '@/components/StandbyWrapper.vue';

export default defineComponent({
  name: 'LoadingOverlay',
  components: {
    ModalWrapper,
    StandbyWrapper,
  },
  computed: {
    ...mapGetters({
      loadingState: 'getLoadingState',
    }),
  },
});
</script>

<style lang="stylus">
.modal-wrapper--loading
  --bgc-loading-circle: rgba(255, 255, 255, 0.4)
  &.modal-wrapper--isVisible
    z-index: $zindex-10
</style>
