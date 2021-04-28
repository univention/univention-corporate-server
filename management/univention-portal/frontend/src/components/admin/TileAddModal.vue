<!--
  Copyright 2021 Univention GmbH

  https://www.univention.de/

  All rights reserved.

  The source code of this program is made available
  under the terms of the GNU Affero General Public License version 3
  (GNU AGPL V3) as published by the Free Software Foundation.

  Binary versions of this program provided by Univention to you as
  well as other copyrighted, protected or trademarked materials like
  Logos, graphics, fonts, specific documentations and configurations,
  cryptographic keys etc. are subject to a license agreement between
  you and Univention and not subject to the GNU AGPL V3.

  In the case you use this program under the terms of the GNU AGPL V3,
  the program is provided in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
  GNU Affero General Public License for more details.

  You should have received a copy of the GNU Affero General Public
  License with the Debian GNU/Linux or Univention distribution in file
  /usr/share/common-licenses/AGPL-3; if not, see
  <https://www.gnu.org/licenses/>.
-->
<template>
  <modal-dialog
    i18n-title-key="ADD_ENTRY"
    @cancel="cancel"
  >
    <button
      class="tile-add-modal-button"
      @click="openModal('createEntry')"
    >
      <translate i18n-key="NEW_ENTRY" />
    </button>
    <button
      class="tile-add-modal-button"
      @click="openModal('addEntry')"
    >
      <translate i18n-key="ADD_EXISTING_ENTRY" />
    </button>
    <button
      class="tile-add-modal-button"
      @click="openModal('addFolder')"
    >
      <translate i18n-key="ADD_EXISTING_FOLDER" />
    </button>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import ModalDialog from '@/components/ModalDialog.vue';
import Translate from '@/i18n/Translate.vue';

export default defineComponent({
  name: 'TileAddModal',
  components: {
    ModalDialog,
    Translate,
  },
  props: {
    categoryDn: {
      type: String,
      required: true,
    },
  },
  methods: {
    openModal(action): void {
      if (action === 'createEntry') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminEntry',
          props: {
            modelValue: {},
            categoryDn: this.categoryDn,
            label: 'ADD_ENTRY',
          },
        });
      }
      if (action === 'addEntry') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminExistingEntry',
          props: {
            label: 'ADD_EXISTING_ENTRY',
            objectGetter: 'portalData/portalEntries',
            categoryDn: this.categoryDn,
          },
        });
      }
      if (action === 'addFolder') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminExistingEntry',
          props: {
            label: 'ADD_EXISTING_FOLDER',
            objectGetter: 'portalData/portalFolders',
            categoryDn: this.categoryDn,
          },
        });
      }
    },
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
    },
  },
});
</script>
<style lang="stylus">
.tile-add-modal-button
    margin: var(--layout-spacing-unit)
</style>
