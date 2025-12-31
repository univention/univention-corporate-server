<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <div class="portal-modal">
    <modal-wrapper
      :is-active="isActiveModal"
      :modal-level="modalLevel"
      @backgroundClick="closeModal"
    >
      <component
        :is="modalComponentLevel"
        v-bind="modalPropsLevel"
      />
    </modal-wrapper>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import ModalWrapper from '@/components/modal/ModalWrapper.vue';
import PortalFolder from '@/components/PortalFolder.vue';
import AdminEntry from '@/components/admin/Entry.vue';
import AdminFolder from '@/components/admin/Folder.vue';
import AdminExistingEntry from '@/components/admin/ExistingEntry.vue';
import AdminCategory from '@/components/admin/FormCategoryEdit.vue';
import AdminExistingCategory from '@/components/admin/ExistingCategory.vue';
import TileAddModal from '@/components/admin/TileAddModal.vue';
import CategoryAddModal from '@/components/admin/CategoryAddModal.vue';
import ConfirmDialog from '@/components/admin/ConfirmDialog.vue';
import AddObjects from '@/components/widgets/AddObjects.vue';
import TranslationEditing from '@/components/admin/TranslationEditing.vue';
import ChooseTabs from '@/components/ChooseTabs.vue';
import LoadingOverlay from '@/components/globals/LoadingOverlay.vue';
import CookieBanner from '@/components/globals/CookieBanner.vue';

export default defineComponent({
  name: 'PortalModal',
  components: {
  // Register and import all possible modal components here
  // Otherwise they will not be displyed correctly
  // (Maybe change PortalModal to not use the component tag anymore?)
    ConfirmDialog,
    AddObjects,
    ModalWrapper,
    PortalFolder,
    AdminEntry,
    AdminFolder,
    AdminExistingEntry,
    AdminCategory,
    AdminExistingCategory,
    ChooseTabs,
    LoadingOverlay,
    TileAddModal,
    CategoryAddModal,
    CookieBanner,
    TranslationEditing,
  },
  props: {
    modalLevel: {
      type: Number,
      default: 1,
    },
  },
  computed: {
    ...mapGetters({
      modalComponent: 'modal/getModalComponent',
      modalProps: 'modal/getModalProps',
      modalStubborn: 'modal/getModalStubborn',
      getModalState: 'modal/getModalState',
    }),
    isActiveModal(): boolean {
      let bool = false;
      if (this.modalLevel === 2) {
        bool = this.getModalState('secondLevelModal');
      }
      if (this.modalLevel === 1) {
        bool = this.getModalState('firstLevelModal');
      }
      return bool;
    },
    modalComponentLevel(): string {
      let component = '';
      if (this.modalLevel === 2) {
        component = this.modalComponent('secondLevelModal');
      }
      if (this.modalLevel === 1) {
        component = this.modalComponent('firstLevelModal');
      }
      return component;
    },
    modalPropsLevel(): Record<string, unknown> {
      let props = {};
      if (this.modalLevel === 2) {
        props = this.modalProps('secondLevelModal');
      }
      if (this.modalLevel === 1) {
        props = this.modalProps('firstLevelModal');
      }
      return props;
    },
  },
  methods: {
    closeModal(): void {
      const modalLevel = this.modalLevel === 2 ? 'secondLevelModal' : 'firstLevelModal';
      if (!this.modalStubborn(modalLevel)) {
        this.$store.dispatch('modal/hideAndClearModal', this.modalLevel);
      }
    },
  },
});
</script>
