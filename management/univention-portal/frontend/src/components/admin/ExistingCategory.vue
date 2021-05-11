<template>
  <modal-dialog
    i18n-title-key="ADD_EXISTING_CATEGORY"
    @cancel="cancel"
  >
    <form
      @submit.prevent="finish"
    >
      <main>
        <label>
          <translate i18n-key="NAME" />
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
            <option
              v-for="item in items"
              :key="item.dn"
              :value="$localized(item.display_name)"
              :data-value="item.dn"
            />
          </datalist>
        </label>
      </main>
      <footer>
        <button
          type="button"
          @click.prevent="cancel"
        >
          <translate i18n-key="CANCEL" />
        </button>
        <button
          class="primary"
          type="submit"
          @click.prevent="finish"
        >
          <translate i18n-key="ADD" />
        </button>
      </footer>
    </form>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import ModalDialog from '@/components/ModalDialog.vue';
import Translate from '@/i18n/Translate.vue';

import { setInvalidity } from '@/jsHelper/tools';
import { put } from '@/jsHelper/admin';

interface ExistingEntryData {
  datalistId: string,
}

export default defineComponent({
  name: 'ExistingCategory',
  components: {
    ModalDialog,
    Translate,
  },
  data(): ExistingEntryData {
    return {
      datalistId: `datalist-${Math.random().toString(36)
        .substr(2, 4)}`,
    };
  },
  computed: {
    ...mapGetters({
      portalDn: 'portalData/getPortalDn',
      categories: 'portalData/portalCategoriesOnPortal',
      items: 'portalData/portalCategories',
    }),
  },
  methods: {
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
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
        console.info('Adding', dn, 'to', this.portalDn);
        await put(this.portalDn, portalAttrs, this.$store, 'CATEGORY_ADDED_SUCCESS', 'CATEGORY_ADDED_FAILURE');
        this.$store.dispatch('deactivateLoadingState');
      }
    },
  },
});
</script>
