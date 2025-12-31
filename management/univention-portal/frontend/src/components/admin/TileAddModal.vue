<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <modal-dialog
    :i18n-title-key="ADD_ENTRY"
    @cancel="cancel"
  >
    <region
      id="tile-add-modal"
      direction="topdown"
    >
      <button
        id="tile-add-modal-button-create-entry"
        tabindex="0"
        class="tile-add-modal-button"
        @click="openModal('createEntry')"
      >
        {{ CREATE_NEW_ENTRY }}
      </button>
      <button
        id="tile-add-modal-button-existing-entry"
        tabindex="0"
        class="tile-add-modal-button"
        @click="openModal('addEntry')"
      >
        {{ CREATE_EXISTING_ENTRY }}
      </button>
      <button
        v-if="!forFolder"
        id="tile-add-modal-button-create-folder"
        tabindex="0"
        class="tile-add-modal-button"
        @click="openModal('createFolder')"
      >
        {{ CREATE_NEW_FOLDER }}
      </button>
      <button
        v-if="!forFolder"
        id="tile-add-modal-button-existing-folder"
        tabindex="0"
        class="tile-add-modal-button"
        @click="openModal('addFolder')"
      >
        {{ CREATE_EXISTING_FOLDER }}
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
  name: 'TileAddModal',
  components: {
    ModalDialog,
    Region,
  },
  props: {
    superDn: {
      type: String,
      required: true,
    },
    forFolder: {
      type: Boolean,
      required: true,
    },
  },
  computed: {
    CREATE_NEW_ENTRY(): string {
      return _('Create a new Entry');
    },
    CREATE_EXISTING_ENTRY(): string {
      return _('Add existing entry');
    },
    CREATE_NEW_FOLDER(): string {
      return _('Create a new folder');
    },
    CREATE_EXISTING_FOLDER(): string {
      return _('Add existing folder');
    },
    ADD_ENTRY(): string {
      return _('Add entry');
    },
  },
  methods: {
    openModal(action: string): void {
      if (action === 'createEntry') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminEntry',
          stubborn: true,
          props: {
            modelValue: {},
            superDn: this.superDn,
            label: this.CREATE_NEW_ENTRY,
            fromFolder: this.forFolder,
          },
        });
      }
      if (action === 'addEntry') {
        let superObjectGetter = 'portalData/portalCategories';
        if (this.forFolder) {
          superObjectGetter = 'portalData/portalFolders';
        }
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminExistingEntry',
          stubborn: true,
          props: {
            label: this.CREATE_EXISTING_ENTRY,
            objectGetter: 'portalData/portalEntries',
            superObjectGetter,
            superDn: this.superDn,
          },
        });
      }
      if (action === 'createFolder') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminFolder',
          stubborn: true,
          props: {
            modelValue: {},
            superDn: this.superDn,
            label: this.CREATE_NEW_FOLDER,
          },
        });
      }
      if (action === 'addFolder') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminExistingEntry',
          stubborn: true,
          props: {
            label: this.CREATE_EXISTING_FOLDER,
            objectGetter: 'portalData/portalFolders',
            superObjectGetter: 'portalData/portalCategories',
            superDn: this.superDn,
          },
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
