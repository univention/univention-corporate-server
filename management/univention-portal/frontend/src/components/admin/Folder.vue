<!--
  Copyright 2021-2022 Univention GmbH

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
    v-model:form-values="formValues"
    :form-widgets="formWidgetsComputed"
    :label="label"
    :can-remove="!!modelValue.dn"
    :model="$data"
    @unlink="unlink"
    @remove="remove"
    @save="finish"
    @submit="submit"
  />
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import { removeEntryFromSuperObj, addEntryToSuperObj, put, add, remove } from '@/jsHelper/admin';
import activity from '@/jsHelper/activity';
import EditWidget from '@/components/admin/EditWidget.vue';
import { validateAll, allValid, validateInternalName } from '@/jsHelper/forms';

interface AdminFolderData {
  formWidgets: any,
  formValues: any,
}

export default defineComponent({
  name: 'FormFolderEdit',
  components: {
    EditWidget,
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
      formWidgets: [{
        type: 'TextBox',
        name: 'name',
        label: _('Internal name'),
        required: true,
        autocomplete: 'off',
        validators: [validateInternalName],
      }, {
        type: 'LocaleInput',
        name: 'title',
        required: true,
        label: _('Name'),
        i18nLabel: _('Name'),
      }],
      formValues: {
        name: '',
        title: {
          en_US: '',
        },
      },
    };
  },
  computed: {
    ...mapGetters({
      portalCategories: 'portalData/portalCategories',
      activityLevel: 'activity/level',
    }),
    formWidgetsComputed(): any {
      return this.formWidgets.map((widget) => {
        if (widget.name === 'name') {
          widget.readonly = !!this.modelValue.dn;
        }
        widget.tabindex = activity(['modal'], this.activityLevel);
        return widget;
      });
    },
  },
  created(): void {
    const dn = this.modelValue.dn;
    if (dn) {
      this.formValues.name = dn.slice(3, dn.indexOf(','));
    }
    const title = this.modelValue.title;
    if (title) {
      this.formValues.title = { ...this.modelValue.title };
    }
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
        name: this.formValues.name,
        displayName: Object.entries(this.formValues.title),
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
    submit() {
      validateAll(this.formWidgets, this.formValues);
      if (!allValid(this.formWidgets)) {
        return;
      }
      this.finish();
    },
  },
});
</script>
