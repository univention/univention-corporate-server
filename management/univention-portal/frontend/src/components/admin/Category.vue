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
    :i18n-title-key="label"
    @cancel="cancel"
  >
    <form
      class="admin-entry"
      @submit.prevent="finish"
    >
      <main>
        <label>
          <translate i18n-key="INTERNAL_NAME" />
          <span> *</span>
          <input
            v-model="name"
            name="name"
            :disabled="modelValue.dn"
          >
        </label>
        <locale-input
          v-model="title"
          label="Name"
        />
      </main>
      <footer
        v-if="modelValue.dn"
      >
        <button
          type="button"
          @click.prevent="remove"
        >
          <translate i18n-key="REMOVE_FROM_PORTAL" />
        </button>
      </footer>
      <footer>
        <button
          type="button"
          @click.prevent="cancel"
        >
          <translate i18n-key="CANCEL" />
        </button>
        <button
          type="submit"
          @click.prevent="finish"
        >
          <translate :i18n-key="label" />
        </button>
      </footer>
    </form>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import { put, add } from '@/jsHelper/admin';
import LocaleInput from '@/components/widgets/LocaleInput.vue';
import ModalDialog from '@/components/ModalDialog.vue';
import Translate from '@/i18n/Translate.vue';

interface AdminCategoryData {
  name: string,
  title: Record<string, string>,
}

export default defineComponent({
  name: 'FormCategoryEdit',
  components: {
    ModalDialog,
    Translate,
    LocaleInput,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    modelValue: {
      type: Object,
      required: true,
    },
  },
  data(): AdminCategoryData {
    return {
      name: '',
      title: {},
    };
  },
  computed: {
    ...mapGetters({
      portalDn: 'portalData/getPortalDn',
      categories: 'portalData/portalCategoriesOnPortal',
    }),
  },
  created(): void {
    const dn = this.modelValue.dn;
    if (dn) {
      this.name = dn.slice(3, dn.indexOf(','));
    }
    this.title = { ...(this.modelValue.title || {}) };
  },
  methods: {
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
    },
    async remove() {
      this.$store.dispatch('activateLoadingState');
      const dn = this.modelValue.dn;
      const portalAttrs = {
        categories: this.categories.filter((catDn) => catDn !== dn),
      };
      console.info('Removing', dn, 'from', this.portalDn);
      put(this.portalDn, portalAttrs, this.$store, 'CATEGORY_REMOVED_SUCCESS', 'CATEGORY_REMOVED_FAILURE');
      this.$store.dispatch('deactivateLoadingState');
    },
    async finish() {
      this.$store.dispatch('activateLoadingState');
      const attrs = {
        name: this.name,
        displayName: Object.entries(this.title),
      };
      if (this.modelValue.dn) {
        console.info('Modifying', this.modelValue.dn);
        put(this.modelValue.dn, attrs, this.$store, 'CATEGORY_MODIFIED_SUCCESS', 'CATEGORY_MODIFIED_FAILURE');
      } else {
        console.info('Adding category');
        console.info('Then adding it to', this.categories, 'of', this.portalDn); // Okay, strange. message needs to be here, otherwise "this" seems to forget its props!
        const dn = await add('portals/category', attrs, this.$store, 'CATEGORY_ADDED_FAILURE');
        if (dn) {
          console.info(dn, 'added');
          const portalAttrs = {
            categories: this.categories.concat([dn]),
          };
          await put(this.portalDn, portalAttrs, this.$store, 'CATEGORY_ADDED_SUCCESS', 'CATEGORY_ADDED_FAILURE');
        }
      }
      this.$store.dispatch('deactivateLoadingState');
    },
  },
});
</script>

<style lang="stylus">
.admin-entry
  width: calc(var(--inputfield-width) + 3rem)
  main
    max-height: 26rem
    overflow: auto
</style>
