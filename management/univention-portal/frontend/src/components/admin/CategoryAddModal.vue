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
    i18n-title-key="ADD_CATEGORY"
    @cancel="cancel"
  >
    <button
      class="tile-add-modal-button"
      @click="openModal('createCategory')"
    >
      <translate i18n-key="ADD_NEW_CATEGORY" />
    </button>
    <button
      class="tile-add-modal-button"
      @click="openModal('addCategory')"
    >
      <translate i18n-key="ADD_EXISTING_CATEGORY" />
    </button>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';

import ModalDialog from '@/components/ModalDialog.vue';
import Translate from '@/i18n/Translate.vue';

export default defineComponent({
  name: 'CategoryAddModal',
  components: {
    ModalDialog,
    Translate,
  },
  methods: {
    openModal(action): void {
      if (action === 'createCategory') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminCategory',
          props: {
            modelValue: {},
            label: 'ADD_CATEGORY',
          },
        });
      }
      if (action === 'addCategory') {
        this.$store.dispatch('modal/setAndShowModal', {
          name: 'AdminExistingCategory',
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
    margin: calc(2 * var(--layout-spacing-unit)) 0
    width: 100%
</style>
