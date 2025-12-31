<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <modal-dialog
    i18n-title-key="ADD_CATEGORY"
    @cancel="cancel"
  >
    <region
      id="category-add-modal"
      direction="topdown"
    >
      <button
        id="category-add-modal-button-create-category"
        tabindex="0"
        class="tile-add-modal-button"
        @click="openModal('createCategory')"
      >
        {{ ADD_NEW_CATEGORY }}
      </button>
      <button
        id="category-add-modal-button-existing-category"
        tabindex="0"
        class="tile-add-modal-button"
        @click="openModal('addCategory')"
      >
        {{ ADD_EXISTING_CATEGORY }}
      </button>
    </region>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import ModalDialog from '@/components/modal/ModalDialog.vue';
import Region from '@/components/activity/Region.vue';

export default defineComponent({
  name: 'CategoryAddModal',
  components: {
    ModalDialog,
    Region,
  },
  computed: {
    ADD_NEW_CATEGORY(): string {
      return _('Add new category');
    },
    ADD_EXISTING_CATEGORY(): string {
      return _('Add existing category');
    },
  },
  methods: {
    openModal(action): void {
      if (action === 'createCategory') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminCategory',
          stubborn: true,
          props: {
            modelValue: {},
            label: _('Add category'),
          },
        });
      }
      if (action === 'addCategory') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminExistingCategory',
          stubborn: true,
        });
      }
    },
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
      this.$store.dispatch('activity/setRegion', 'portalCategories');
    },
  },
});
</script>
<style lang="stylus">
.tile-add-modal-button
    margin: calc(2 * var(--layout-spacing-unit)) 0
    width: 100%
</style>
