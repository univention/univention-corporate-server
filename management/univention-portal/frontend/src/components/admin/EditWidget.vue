<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <modal-dialog
    :i18n-title-key="label"
    @cancel="cancel"
  >
    <my-form
      ref="form"
      class="admin-entry"
      :widgets="formWidgets"
      :model-value="formValues"
      @update:model-value="$emit('update:formValues', $event)"
    >
      <footer
        v-if="canRemove"
      >
        <button
          type="button"
          :tabindex="tabindex"
          @click.prevent="openConfirmationDialog"
        >
          {{ REMOVE }}
        </button>
      </footer>
      <footer>
        <button
          type="button"
          :tabindex="tabindex"
          @click.prevent="cancel"
        >
          {{ CANCEL }}
        </button>
        <button
          class="button--primary"
          type="submit"
          :tabindex="tabindex"
          @click.prevent="submit"
        >
          {{ SAVE }}
        </button>
      </footer>
    </my-form>
  </modal-dialog>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';
import MyForm from '@/components/forms/Form.vue';

import activity from '@/jsHelper/activity';
import ModalDialog from '@/components/modal/ModalDialog.vue';

export default defineComponent({
  name: 'EditWidget',
  components: {
    MyForm,
    ModalDialog,
  },
  props: {
    label: {
      type: String,
      required: true,
    },
    canRemove: {
      type: Boolean,
      required: true,
    },
    formWidgets: {
      type: Array,
      required: true,
    },
    formValues: {
      type: Object,
      required: true,
    },
  },
  emits: ['unlink', 'remove', 'save', 'update:formValues', 'submit'],
  computed: {
    ...mapGetters({
      activityLevel: 'activity/level',
    }),
    tabindex(): number {
      // Sets to tabindex -1 if modalLevel 2 is active
      return activity(['modal'], this.activityLevel);
    },
    SAVE(): string {
      return _('Save');
    },
    CANCEL(): string {
      return _('Cancel');
    },
    REMOVE(): string {
      return _('Remove');
    },
  },
  mounted() {
    // @ts-ignore TODO
    this.$refs.form.focusFirstInteractable();
  },
  methods: {
    cancel() {
      this.$store.dispatch('modal/hideAndClearModal');
      this.$store.dispatch('activity/setRegion', 'portalCategories');
    },
    submit() {
      this.$emit('submit');
    },
    openConfirmationDialog() {
      this.$store.dispatch('modal/setShowModalPromise', {
        level: 2,
        name: 'ConfirmDialog',
        stubborn: true,
      }).then((values) => {
        this.$store.dispatch('modal/hideAndClearModal', 2);
        if (values.action === 'remove') {
          this.$emit('remove');
        } else if (values.action === 'unlink') {
          this.$emit('unlink');
        }
      }, () => {
        this.$store.dispatch('modal/hideAndClearModal', 2);
      });
    },
  },
});
</script>

<style lang="stylus">
.admin-entry
  .form-element
    input[type="text"],
    textarea,
    select
      width: 100%
</style>
