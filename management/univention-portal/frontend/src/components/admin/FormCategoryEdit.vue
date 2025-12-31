<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
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

import { put, add, remove } from '@/jsHelper/admin';
import activity from '@/jsHelper/activity';
import EditWidget from '@/components/admin/EditWidget.vue';
import { validateAll, allValid, validateInternalName } from '@/jsHelper/forms';

interface AdminCategoryData {
  formWidgets: any,
  formValues: any,
}

export default defineComponent({
  name: 'FormCategoryEdit',
  components: {
    EditWidget,
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
      portalDn: 'portalData/getPortalDn',
      categories: 'portalData/portalCategoriesOnPortal',
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
      const portalAttrs = {
        categories: this.categories.filter((catDn) => catDn !== dn),
      };
      // console.info('Removing', dn, 'from', this.portalDn);
      const success = await put(this.portalDn, portalAttrs, this.$store, _('Category could not be unlinked'), _('Category successfully unlinked'));
      this.$store.dispatch('deactivateLoadingState');
      if (success) {
        this.cancel();
      }
    },
    async remove() {
      this.$store.dispatch('activateLoadingState');
      const dn = this.modelValue.dn;
      // console.info('Deleting', dn, 'completely');
      const success = await remove(dn, this.$store, _('Category successfully removed'), _('Category could not be removed'));
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
        success = await put(this.modelValue.dn, attrs, this.$store, _('Category could not be modified'), _('Category successfully modified'));
      } else {
        // console.info('Adding category');
        // console.info('Then adding it to', this.categories, 'of', this.portalDn); // Okay, strange. message needs to be here, otherwise "this" seems to forget its props!
        const dn = await add('portals/category', attrs, this.$store, _('Category could not be added'));
        if (dn) {
          // console.info(dn, 'added');
          const portalAttrs = {
            categories: this.categories.concat([dn]),
          };
          success = await put(this.portalDn, portalAttrs, this.$store, _('Category could not be added'), _('Category successfully added'));
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
