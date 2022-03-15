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
  <modal-dialog
    :id="id"
    :title="TRANSLATION_OF"
    :modal-level="modalLevel"
    @cancel="cancel"
  >
    <my-form
      ref="form"
      v-model="formValues"
      :widgets="formWidgets"
    >
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
          @click.prevent="save"
        >
          {{ SAVE }}
        </button>
      </footer>
    </my-form>
  </modal-dialog>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

import ModalDialog from '@/components/modal/ModalDialog.vue';
import MyForm from '@/components/forms/Form.vue';
import { allValid, validateAll } from '@/jsHelper/forms';

export default defineComponent({
  name: 'TranslationEditing',
  components: {
    ModalDialog,
    MyForm,
  },
  props: {
    title: {
      type: String,
      default: 'REMOVE',
    },
    inputValue: {
      type: Object,
      required: true,
    },
    modalLevelProp: {
      type: Number,
      required: true,
    },
  },
  data() {
    return {
      id: '',
      formWidgets: [],
      formValues: {},
    };
  },
  computed: {
    ...mapGetters({
      locales: 'locale/getAvailableLocales',
      localeLabels: 'locale/getLocaleLabels',
    }),
    TRANSLATION_OF(): string {
      return _('Translation: %(key1)s', { key1: this.title });
    },
    CANCEL(): string {
      return _('Cancel');
    },
    SAVE(): string {
      return _('Save');
    },
    modalLevel(): string {
      // Modal 2 Because it set the correct tabindizies for elements in modal Level 1
      return 'modal2';
    },
  },
  mounted() {
    this.id = 'translation-editing';

    const formWidgets: any = [];
    const formValues = {};
    this.locales.forEach((locale) => {
      const widget = {
        type: 'TextBox',
        name: locale,
        label: this.localeLabels[locale] || locale,
        placeholder: this.inputValue[locale] ? null : this.inputValue.en_US,
        required: false,
      };
      if (locale === 'en_US') {
        widget.required = true;
      }
      formWidgets.push(widget);
      formValues[locale] = this.inputValue[locale] ?? '';
    });
    this.formWidgets = formWidgets;
    this.formValues = formValues;

    this.$nextTick(() => {
      // @ts-ignore TODO
      this.$refs.form.focusFirstInteractable();
    });
  },
  methods: {
    cancel(): void {
      this.$store.dispatch('modal/reject', this.modalLevelProp);
    },
    save(): void {
      validateAll(this.formWidgets, this.formValues);
      if (!allValid(this.formWidgets)) {
        // @ts-ignore TODO
        this.$refs.form.focusFirstInvalid();
        return;
      }
      this.$store.dispatch('modal/resolve', {
        level: this.modalLevelProp,
        translations: this.formValues,
      });
    },
  },
});

</script>

<style lang="stylus">
#translation-editing
  input
    width: 100%
</style>
