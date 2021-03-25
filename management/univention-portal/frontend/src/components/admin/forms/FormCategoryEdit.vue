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
  <div>
    <div class="modal-admin__layout-row">
      <div class="form-input__wrapper">
        <label class="form-input__label">
          <translate i18n-key="INTERNAL_NAME" />
          <span> *</span>
        </label>
        <div
          class="form-input__container"
        >
          <input
            v-model="categoryForm.internalName"
            type="text"
            :placeholder="INTERNAL_NAME"
            :disabled="true"
            class="form-input--default form-input--text"
            name="internalName"
            autocomplete="off"
            tabindex="0"
            aria-required="true"
            aria-invalid="false"
          >
        </div>
      </div>
    </div>

    <div class="modal-admin__layout-row">
      <div>
        <label class="modal-admin__label">
          <translate i18n-key="DISPLAY_NAME" /> *
        </label>
        <span class="modal-admin__hint-wrapper">
          <portal-icon
            icon="help-circle"
            icon-width="2rem"
            class="modal-admin__hint-icon"
            @click="toggleHint()"
          />
          <span
            v-if="showHint"
            class="modal-admin__hint"
          >
            <div class="modal-admin__hint-connector" />
            <div
              class="modal-admin__hint-content"
              role="alert"
            >
              <translate i18n-key="MODAL_HINT_CATEGORIES" />
            </div>
          </span>
        </span>
      </div>

      <div class="form-input__wrapper">
        <label class="form-input__label">
          <translate i18n-key="LANGUAGE_CODE" />
          <span v-if="inputMandatory"> *</span>
        </label>
        <div
          class="form-input__container"
        >
          <input
            v-model="categoryForm.key.de_DE"
            type="text"
            :placeholder="LANGUAGE_CODE"
            :disabled="true"
            class="form-input--default form-input--text"
            name="key.de_DE"
            autocomplete="off"
            tabindex="0"
            aria-required="true"
            aria-invalid="false"
          >
        </div>
      </div>

      <div class="form-input__wrapper">
        <label
          :class="{'form-input__label--error' : formErrors.error.title_de.error}"
          class="form-input__label"
        >
          <translate i18n-key="DISPLAY_NAME" />
          <span v-if="inputMandatory"> *</span>
        </label>
        <portal-icon
          v-if="formErrors.error.title_de.error"
          class="form-input__icon--error"
          icon="alert-circle"
          icon-width="2rem"
        />
        <div
          class="form-input__container"
        >
          <input
            v-model="categoryForm.title.de_DE"
            type="text"
            :placeholder="DISPLAY_NAME"
            :class="{'form-input--error' : formErrors.error.title_de.error}"
            class="form-input--default form-input--text"
            name="title.de_DE"
            autocomplete="off"
            tabindex="0"
            aria-required="true"
            aria-invalid="false"
            @blur="checkInput($event, 'blur')"
            @keyup="checkInput($event, 'keyup')"
          >
        </div>
        <!-- <span
          v-if="formErrors.error.title_de.error"
          class="form-input__error-message"
        >
          {{ $localized(formErrors.error.title_de.message) }}
        </span> -->
      </div>

      <div class="form-input__wrapper">
        <label class="form-input__label">
          <translate i18n-key="LANGUAGE_CODE" />
          <span v-if="inputMandatory"> *</span>
        </label>
        <div
          class="form-input__container"
        >
          <input
            v-model="categoryForm.key.en_US"
            type="text"
            :placeholder="LANGUAGE_CODE"
            :disabled="true"
            class="form-input--default form-input--text"
            name="key.en_US"
            autocomplete="off"
            tabindex="0"
            aria-required="true"
            aria-invalid="false"
          >
        </div>
      </div>

      <div class="form-input__wrapper">
        <label
          :class="{'form-input__label--error' : formErrors.error.title_en.error}"
          class="form-input__label"
        >
          <translate i18n-key="DISPLAY_NAME" />
          <span v-if="inputMandatory"> *</span>
        </label>
        <portal-icon
          v-if="formErrors.error.title_en.error"
          class="form-input__icon--error"
          icon="alert-circle"
          icon-width="2rem"
        />
        <div
          class="form-input__container"
        >
          <input
            v-model="categoryForm.title.en_US"
            type="text"
            :placeholder="DISPLAY_NAME"
            :class="{'form-input--error' : formErrors.error.title_en.error}"
            class="form-input--default form-input--text"
            name="title.en_US"
            autocomplete="off"
            tabindex="0"
            aria-required="true"
            aria-invalid="false"
            @blur="checkInput($event, 'blur')"
            @keyup="checkInput($event, 'keyup')"
          >
        </div>
        <!-- <span
          v-if="formErrors.error.title_en.error"
          class="form-input__error-message"
        >
          {{ $localized(formErrors.error.title_en.message) }}
        </span> -->
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted, computed } from 'vue';

import PortalIcon from '@/components/globals/PortalIcon.vue';

import Translate from '@/i18n/Translate.vue';

export default defineComponent({
  name: 'FormCategoryEdit',
  components: {
    PortalIcon,
    Translate,
  },
  props: {
    modelValue: {
      type: Object,
      required: true,
    },
  },
  emits: [
    'closeModal',
    'removeCategory',
    'saveCategory',
    'update:modelValue',
  ],
  setup(props, { emit }) {
    // data
    const showHint = ref(false);

    const formErrors = reactive({
      error: {
        title_de: {
          error: false,
          message: {
            de_DE: 'Eingabe fehlt!',
            en_EN: 'Value missing!',
          },
        },
        title_en: {
          error: false,
          message: {
            de_DE: 'Eingabe fehlt!',
            en_EN: 'Value missing!',
          },
        },
      },
    });

    // v-model
    const categoryForm = computed({
      get: () => props.modelValue,
      set: (value) => emit('update:modelValue', value),
    });

    // methods
    const toggleHint = () => {
      // HINT: the Vue3 way
      showHint.value = !showHint.value;
    };

    const checkInput = (e, action) => {
      // console.log('checkInput: ', action, e.target.value);

      if ((e.target.value === '') && (action === 'blur')) {
        switch (e.target.name) {
          case 'internalName':
            formErrors.error.internalName.error = true;
            break;
          case 'title.de_DE':
            formErrors.error.title_de.error = true;
            break;
          case 'title.en_US':
            formErrors.error.title_en.error = true;
            break;
          default:
            // nothing defined
        }
      }

      if (e.target.value !== '' && action === 'keyup') {
        switch (e.target.name) {
          case 'internalName':
            formErrors.error.internalName.error = false;
            break;
          case 'title.de_DE':
            formErrors.error.title_de.error = false;
            break;
          case 'title.en_US':
            formErrors.error.title_en.error = false;
            break;
          default:
            // nothing defined
        }
      }
    };

    // mounted
    onMounted(() => {
      // set focus on first visible input
      let i = 0;

      for (i; document.forms[0].elements[i].type === 'hidden'; i += 1);
      document.forms[0].elements[i].focus();
    });

    return {
      showHint,
      categoryForm,
      formErrors,
      toggleHint,
      checkInput,
    };
  },
});
</script>
