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
        <label>
          <input
            v-model="activated"
            type="checkbox"
          >
          <translate i18n-key="ACTIVATED" />
        </label>
        <locale-input
          v-model="title"
          label="Name"
        />
        <locale-input
          v-model="description"
          label="Description"
        />
        <div
          v-for="(link, index) in links"
          :key="index"
          class="admin-entry__spacer"
        >
          <locale-input
            v-model="links[index]"
            label="Links"
          />
          <span
            v-if="links.length > 1"
            class="modal-admin__button"
          >
            <button
              class="modal-admin__button--inner"
              @click.prevent="removeField(index, links)"
            >
              <portal-icon
                icon="trash"
              />
              <translate
                i18n-key="REMOVE"
              />
            </button>
          </span>
        </div>

        <span class="modal-admin__button">
          <button
            class="modal-admin__button--inner"
            @click.prevent="addField(links)"
          >
            <portal-icon
              icon="plus"
            />
            <translate
              i18n-key="NEW_ENTRY"
            />
          </button>
        </span>

        <image-upload
          v-model="pathToLogo"
          label="Icon"
        />
        <label>
          <translate i18n-key="BACKGROUND_COLOR" />
          <input
            v-model="backgroundColor"
            name="backgroundColor"
          >
        </label>
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

import { udmPut, udmAdd } from '@/jsHelper/umc';
import ImageUpload from '@/components/widgets/ImageUpload.vue';
import LocaleInput from '@/components/widgets/LocaleInput.vue';
import ModalDialog from '@/components/ModalDialog.vue';
import PortalIcon from '@/components/globals/PortalIcon.vue';

import Translate from '@/i18n/Translate.vue';

interface AdminEntryData {
  name: string,
  activated: boolean,
  pathToLogo: string,
  backgroundColor: string | null,
  title: Record<string, string>,
  description: Record<string, string>,
  links: Array<unknown>,
}

export default defineComponent({
  name: 'FormEntryEdit',
  components: {
    ModalDialog,
    Translate,
    ImageUpload,
    LocaleInput,
    PortalIcon,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    categoryDn: {
      type: String,
      required: true,
    },
    modelValue: {
      type: Object,
      required: true,
    },
  },
  data(): AdminEntryData {
    return {
      name: '',
      activated: true,
      pathToLogo: '',
      title: {},
      description: {},
      backgroundColor: null,
      links: [],
    };
  },
  computed: {
    ...mapGetters({
      portalCategories: 'portalData/portalCategories',
    }),
  },
  created(): void {
    const dn = this.modelValue.dn;
    const activated = this.modelValue.activated;
    if (dn) {
      this.name = dn.slice(3, dn.indexOf(','));
    }
    if (activated !== undefined) {
      this.activated = activated;
    }
    this.pathToLogo = this.modelValue.pathToLogo || '';
    this.backgroundColor = this.modelValue.backgroundColor || null;
    this.title = { ...(this.modelValue.title || {}) };
    this.description = { ...(this.modelValue.description || {}) };
    this.links.push(...(this.modelValue.links));
  },
  methods: {
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
    },
    async remove() {
      const dn = this.modelValue.dn;
      const category = this.portalCategories.find((cat) => cat.dn === this.categoryDn);
      const categoryAttrs = {
        entries: category.entries.filter((entryDn) => entryDn !== dn),
      };
      console.info('Removing', dn, 'from', this.categoryDn);
      try {
        await udmPut(this.categoryDn, categoryAttrs);
        this.$store.dispatch('notificationBubble/addSuccessNotification', {
          bubbleTitle: this.$translateLabel('ENTRY_REMOVED_SUCCESS'),
        });
      } catch (err) {
        console.error(err.message);
        this.$store.dispatch('notificationBubble/addErrorNotification', {
          bubbleTitle: this.$translateLabel('ENTRY_REMOVED_FAILURE'),
        });
      }
      this.$store.dispatch('modal/hideAndClearModal');
    },
    async finish() {
      const attrs = {
        name: this.name,
        activated: this.activated,
        pathToLogo: this.pathToLogo,
        title: this.title,
      };
      if (this.modelValue.dn) {
        console.info('Modifying', this.modelValue.dn);
        try {
          await udmPut(this.modelValue.dn, attrs);
          this.$store.dispatch('notificationBubble/addSuccessNotification', {
            bubbleTitle: this.$translateLabel('ENTRY_MODIFIED_SUCCESS'),
          });
        } catch (err) {
          console.error(err.message);
          this.$store.dispatch('notificationBubble/addErrorNotification', {
            bubbleTitle: this.$translateLabel('ENTRY_MODIFIED_FAILURE'),
          });
        }
      } else {
        try {
          console.info('Adding entry');
          const response = await udmAdd('portals/category', attrs);
          const dn = response.data.result[0].$dn$;
          console.info(dn, 'added');
          const category = this.portalCategories.find((cat) => cat.dn === this.categoryDn);
          const categoryAttrs = {
            entries: category.entries.concat([dn]),
          };
          await udmPut(this.categoryDn, categoryAttrs);
          this.$store.dispatch('notificationBubble/addSuccessNotification', {
            bubbleTitle: this.$translateLabel('ENTRY_CREATED_SUCCESS'),
          });
        } catch (err) {
          console.error(err.message);
          this.$store.dispatch('notificationBubble/addErrorNotification', {
            bubbleTitle: this.$translateLabel('ENTRY_CREATED_FAILURE'),
          });
        }
      }
      this.$store.dispatch('modal/hideAndClearModal');
    },

    addField(fieldType) {
      fieldType.push({ value: '' });
    },

    removeField(index, fieldType) {
      // TODO: does not yet remove the selected element
      console.log('this.links: ', this.links);
      console.log('index: ', index);
      console.log('fieldType before: ', JSON.parse(JSON.stringify(fieldType)));

      fieldType.splice(index, 1);

      const test = JSON.parse(JSON.stringify(fieldType));
      // test.splice(index, 1);

      console.log('test: ', test);
      this.links = [];
      console.log('this.links: ', this.links);
      this.links.push(...(test));
      console.log('this.links: ', this.links);
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

  &__spacer
    margin: calc(var(--layout-spacing-unit) * 5) auto
</style>
