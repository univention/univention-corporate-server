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
  <edit-widget
    :label="label"
    :can-remove="!!modelValue.dn"
    @remove="remove"
    @save="finish"
  >
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
  </edit-widget>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import { put, add } from '@/jsHelper/admin';
import EditWidget from '@/components/admin/EditWidget.vue';
import ImageUpload from '@/components/widgets/ImageUpload.vue';
import LocaleInput from '@/components/widgets/LocaleInput.vue';
import LinkWidget from '@/components/widgets/LinkWidget.vue';

import Translate from '@/i18n/Translate.vue';

interface AdminFolderData {
  name: string,
  title: Record<string, string>,
}

export default defineComponent({
  name: 'FormFolderEdit',
  components: {
    ImageUpload,
    EditWidget,
    LocaleInput,
    LinkWidget,
    Translate,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    superDn: {
      type: String,
      required: true,
    },
    modelValue: {
      type: Object,
      required: true,
    },
  },
  data(): AdminFolderData {
    return {
      name: '',
      title: {},
    };
  },
  computed: {
    ...mapGetters({
      portalCategories: 'portalData/portalCategories',
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
      const category = this.portalCategories.find((cat) => cat.dn === this.superDn);
      const categoryAttrs = {
        entries: category.entries.filter((entryDn) => entryDn !== dn),
      };
      console.info('Removing', dn, 'from', this.superDn);
      await put(this.superDn, categoryAttrs, this.$store, 'FOLDER_REMOVED_SUCCESS', 'FOLDER_REMOVED_FAILURE');
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
        await put(this.modelValue.dn, attrs, this.$store, 'FOLDER_MODIFIED_SUCCESS', 'FOLDER_MODIFIED_FAILURE');
      } else {
        console.info('Adding folder');
        const dn = await add('portals/folder', attrs, this.$store, 'FOLDER_ADDED_FAILURE');
        if (dn) {
          console.info(dn, 'added');
          const category = this.portalCategories.find((cat) => cat.dn === this.superDn);
          const categoryAttrs = {
            entries: category.entries.concat([dn]),
          };
          await put(this.superDn, categoryAttrs, this.$store, 'FOLDER_ADDED_SUCCESS', 'FOLDER_ADDED_FAILURE');
        }
      }
      this.$store.dispatch('deactivateLoadingState');
    },
  },
});
</script>
