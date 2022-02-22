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
    :i18n-title-key="ADD_EXISTING_CATEGORY"
    @cancel="cancel"
  >
    <form
      @submit.prevent="finish"
    >
      <main>
        <label>
          {{ NAME }}
          <input
            ref="input"
            type="text"
            autocomplete="off"
            :list="datalistId"
            name="display_name"
          >
          <datalist
            :id="datalistId"
          >
            <template
              v-for="item in items"
              :key="item.dn"
            >
              <option
                v-if="!item.virtual"
                :value="$localized(item.display_name)"
                :data-value="item.dn"
              />
            </template>
          </datalist>
        </label>
      </main>
      <footer>
        <button
          type="button"
          @click.prevent="cancel"
        >
          {{ CANCEL }}
        </button>
        <button
          class="primary"
          type="submit"
          @click.prevent="finish"
        >
          {{ ADD }}
        </button>
      </footer>
    </form>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import ModalDialog from '@/components/modal/ModalDialog.vue';

import { setInvalidity, randomId } from '@/jsHelper/tools';
import { put } from '@/jsHelper/admin';

interface ExistingEntryData {
  datalistId: string,
}

export default defineComponent({
  name: 'ExistingCategory',
  components: {
    ModalDialog,
  },
  data(): ExistingEntryData {
    return {
      datalistId: `datalist-${randomId()}`,
    };
  },
  computed: {
    ...mapGetters({
      portalDn: 'portalData/getPortalDn',
      categories: 'portalData/portalCategoriesOnPortal',
      items: 'portalData/portalCategories',
    }),
    NAME(): string {
      return _('Name');
    },
    CANCEL(): string {
      return _('Cancel');
    },
    ADD(): string {
      return _('Add');
    },
    ADD_EXISTING_CATEGORY(): string {
      return _('Add existing category');
    },
  },
  mounted() {
    this.$el.querySelector('input:enabled')?.focus();
  },
  methods: {
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
      this.$store.dispatch('activity/setRegion', 'portalCategories');
    },
    async finish() {
      const input = this.$refs.input as HTMLFormElement;
      const list = input.getAttribute('list');
      const options = document.querySelectorAll(`#${list} option`);

      let dn: string | null = null;
      for (let k = 0; k < options.length; k += 1) {
        const option = options[k];

        if (option.getAttribute('value') === input.value) {
          dn = option.getAttribute('data-value');
          break;
        }
      }
      setInvalidity(this, 'input', !dn);
      if (dn) {
        this.$store.dispatch('activateLoadingState');
        const portalAttrs = {
          categories: this.categories.concat([dn]),
        };
        // console.info('Adding', dn, 'to', this.portalDn);
        const success = await put(this.portalDn, portalAttrs, this.$store, _('Category could not be added'), _('Category successfully added'));
        this.$store.dispatch('deactivateLoadingState');
        if (success) {
          this.cancel();
        }
      }
    },
  },
});
</script>
<style>
</style>
