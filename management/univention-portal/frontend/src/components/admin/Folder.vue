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
    @unlink="unlink"
    @remove="remove"
    @save="finish"
  >
    <h3 class="sr-only sr-only-mobile">
      {{ INTERNAL_NAME_SR_ONLY }}
    </h3>
    <label>
      {{ INTERNAL_NAME }}
      {{ READ_ONLY }}
      <required-field-label
        v-if="!modelValue.dn"
      />
      <input
        v-model="name"
        :tabindex="tabindex"
        :readonly="modelValue.dn"
        class="folder__text-input"
        name="name"
        autocomplete="off"
      >
    </label>
    <locale-input
      v-model="title"
      :i18n-label="NAME"
      name="title"
      :tabindex="tabindex"
    />
  </edit-widget>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import { removeEntryFromSuperObj, addEntryToSuperObj, put, add, remove } from '@/jsHelper/admin';
import activity from '@/jsHelper/activity';
import EditWidget, { ValidatableData } from '@/components/admin/EditWidget.vue';
import ImageUpload from '@/components/widgets/ImageUpload.vue';
import LocaleInput from '@/components/widgets/LocaleInput.vue';
import RequiredFieldLabel from '@/components/forms/RequiredFieldLabel.vue';

interface AdminFolderData extends ValidatableData {
  name: string,
  title: Record<string, string>,
}

function getErrors(this: AdminFolderData) {
  const errors: Record<string, string> = {};
  if (!this.name) {
    errors.name = _('Please enter an internal name');
  } else {
    const regex = new RegExp('(^[a-zA-Z0-9])[a-zA-Z0-9._-]*([a-zA-Z0-9]$)');
    if (!regex.test(this.name)) {
      errors.name = _('Internal name must not contain anything other than digits, letters or dots, must be at least 2 characters long, and start and end with a digit or letter!');
    }
  }
  if (!this.title.en_US) {
    errors.title = _('Please enter a display name');
  }
  return errors;
}

export default defineComponent({
  name: 'FormFolderEdit',
  components: {
    ImageUpload,
    EditWidget,
    LocaleInput,
    RequiredFieldLabel,
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
      getErrors,
    };
  },
  computed: {
    ...mapGetters({
      portalCategories: 'portalData/portalCategories',
      activityLevel: 'activity/level',
    }),
    INTERNAL_NAME(): string {
      return _('Internal name');
    },
    INTERNAL_NAME_SR_ONLY(): string {
      return `${this.name} ${this.INTERNAL_NAME} ${_('view-only')}`;
    },
    READ_ONLY(): string | null {
      return this.modelValue.dn ? `(${_('readonly')})` : null;
    },
    NAME(): string {
      return _('Name');
    },
    tabindex(): number {
      return activity(['modal'], this.activityLevel);
    },
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
      this.$store.dispatch('activity/setRegion', 'portalCategories');
    },
    async unlink() {
      this.$store.dispatch('activateLoadingState');
      const dn = this.modelValue.dn;
      // console.info('Removing', dn, 'from', this.superDn);
      const success = await removeEntryFromSuperObj(this.superDn, this.portalCategories, dn, this.$store, _('Folder successfully unlinked'), _('Folder could not be unlinked'));
      this.$store.dispatch('deactivateLoadingState');
      if (success) {
        this.cancel();
      }
    },
    async remove() {
      this.$store.dispatch('activateLoadingState');
      const dn = this.modelValue.dn;
      // console.info('Deleting', dn, 'completely');
      const success = await remove(dn, this.$store, _('Folder successfully removed'), _('Folder could not be removed'));
      this.$store.dispatch('deactivateLoadingState');
      if (success) {
        this.cancel();
      }
    },
    async finish() {
      this.$store.dispatch('activateLoadingState');
      let success = false;
      const attrs = {
        name: this.name,
        displayName: Object.entries(this.title),
      };
      if (this.modelValue.dn) {
        // console.info('Modifying', this.modelValue.dn);
        success = await put(this.modelValue.dn, attrs, this.$store, _('Folder could not be modified'), _('Folder successfully modified'));
      } else {
        // console.info('Adding folder');
        const dn = await add('portals/folder', attrs, this.$store, _('Folder could not be added'));
        if (dn) {
          // console.info(dn, 'added');
          success = await addEntryToSuperObj(this.superDn, this.portalCategories, dn, this.$store, _('Folder successfully added'), _('Folder could not be added'));
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
<style lang="stylus">
.folder
  &__text-input
    width: 100%
</style>
