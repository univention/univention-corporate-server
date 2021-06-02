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
    :model="$data"
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
      name="title"
      i18n-label="NAME"
    />
    <locale-input
      v-model="description"
      name="description"
      i18n-label="DESCRIPTION"
    />
    <label>
      <input
        v-model="activated"
        type="checkbox"
      >
      <translate i18n-key="ACTIVATED" />
    </label>
    <div>
      <label>
        Links
      </label>
      <link-widget
        v-model="links"
        name="links"
      />
    </div>

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
  </edit-widget>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

import { put, add } from '@/jsHelper/admin';
import EditWidget, { ValidatableData } from '@/components/admin/EditWidget.vue';
import ImageUpload from '@/components/widgets/ImageUpload.vue';
import LocaleInput from '@/components/widgets/LocaleInput.vue';
import LinkWidget, { LocaleAndValue } from '@/components/widgets/LinkWidget.vue';

import Translate from '@/i18n/Translate.vue';

interface AdminEntryData extends ValidatableData {
  name: string,
  activated: boolean,
  pathToLogo: string,
  backgroundColor: string | null,
  title: Record<string, string>,
  description: Record<string, string>,
  links: Array<LocaleAndValue>,
}

function getErrors(this: AdminEntryData) {
  const errors: Record<string, string> = {};
  if (!this.name) {
    errors.name = 'ERROR_ENTER_NAME';
  } else {
    const regex = new RegExp('(^[a-zA-Z0-9])[a-zA-Z0-9._-]*([a-zA-Z0-9]$)');
    if (!regex.test(this.name)) {
      errors.name = 'ERROR_WRONG_NAME';
    }
  }
  if (!this.title.en_US) {
    errors.title = 'ERROR_ENTER_TITLE';
  }
  if (!this.description.en_US) {
    errors.description = 'ERROR_ENTER_DESCRIPTION';
  }
  if (!this.links.some((link) => link.locale === 'en_US' && !!link.value)) {
    errors.links = 'ERROR_ENTER_LINK';
  }
  if (this.links.length === 0) {
    errors.links = 'ERROR_ENTER_LINK';
  }
  return errors;
}

export default defineComponent({
  name: 'FormEntryEdit',
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
    fromFolder: {
      type: Boolean,
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
      getErrors,
    };
  },
  computed: {
    ...mapGetters({
      portalCategories: 'portalData/portalCategories',
      portalFolders: 'portalData/portalFolders',
    }),
    superObjs(): any[] {
      if (this.fromFolder) {
        return this.portalFolders;
      }
      return this.portalCategories;
    },
  },
  created(): void {
    console.info('Edit entry', this.modelValue);
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
    this.links.push(...(this.modelValue.links || []));
  },
  methods: {
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
      this.$store.dispatch('activity/setRegion', 'portalCategories');
    },
    async remove() {
      this.$store.dispatch('activateLoadingState');
      const dn = this.modelValue.dn;
      const superObj = this.superObjs.find((obj) => obj.dn === this.superDn);
      const superAttrs = {
        entries: superObj.entries.filter((entryDn) => entryDn !== dn),
      };
      console.info('Removing', dn, 'from', this.superDn);
      const success = await put(this.superDn, superAttrs, this.$store, 'ENTRY_REMOVED_SUCCESS', 'ENTRY_REMOVED_FAILURE');
      this.$store.dispatch('deactivateLoadingState');
      if (success) {
        this.cancel();
      }
    },
    async finish() {
      this.$store.dispatch('activateLoadingState');
      let success = false;
      const links = this.links.filter((lnk) => !!lnk.value).map((lnk) => [lnk.locale, lnk.value]);
      const attrs = {
        name: this.name,
        activated: this.activated,
        displayName: Object.entries(this.title),
        description: Object.entries(this.description),
        link: links,
        icon: '',
        backgroundColor: this.backgroundColor,
      };
      if (this.pathToLogo.startsWith('data:')) {
        attrs.icon = this.pathToLogo.split(',')[1];
      } else if (this.pathToLogo === '') {
        attrs.icon = '';
      } else {
        delete attrs.icon;
      }

      if (this.modelValue.dn) {
        console.info('Modifying', this.modelValue.dn);
        success = await put(this.modelValue.dn, attrs, this.$store, 'ENTRY_MODIFIED_SUCCESS', 'ENTRY_MODIFIED_FAILURE');
      } else {
        console.info('Adding entry');
        console.info('Then adding it to', [...this.superObjs], 'of', this.superDn); // Okay, strange. message needs to be here, otherwise "this" seems to forget its props!
        const dn = await add('portals/entry', attrs, this.$store, 'ENTRY_ADDED_FAILURE');
        if (dn) {
          console.info(dn, 'added');
          const superObj = this.superObjs.find((obj) => obj.dn === this.superDn);
          const superAttrs = {
            entries: superObj.entries.concat([dn]),
          };
          success = await put(this.superDn, superAttrs, this.$store, 'ENTRY_ADDED_SUCCESS', 'ENTRY_ADDED_FAILURE');
        }
      }
      this.$store.dispatch('deactivateLoadingState');
      if (success) {
        this.cancel();
      }
    },
  },
});
</script>
