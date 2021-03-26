<template>
  <div v-if="categoryListing">
    <div class="modal-admin__layout-row">
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
        <!-- <portal-icon
          class="form-input__icon"
          icon="chevron-down"
          icon-width="2rem"
        /> -->
        <div
          class="form-input__container"
        >
          <input
            v-model="categoryForm.internalName"
            type="text"
            :placeholder="INTERNAL_NAME"
            :list="dataList"
            :class="{'form-input--error' : formErrors.error.internalName.error}"
            class="form-input--default form-input--text"
            name="internalName"
            autocomplete="off"
            tabindex="0"
            aria-required="true"
            aria-invalid="false"
            @blur="checkInput($event, 'blur')"
            @keyup="checkInput($event, 'keyup')"
          >
          <datalist
            id="categoryList"
          >
            <option
              v-for="(item, index) in categoryListing"
              :key="index"
              :value="item"
            />
          </datalist>
        </div>
        <!-- <span
          v-if="formErrors.error.title_de.error"
          class="form-input__error-message"
        >
          {{ $localized(formErrors.error.title_de.message) }}
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
  name: 'FormCategoryAddNew',
  components: {
    PortalIcon,
    Translate,
  },
  props: {
    modelValue: {
      type: Object,
      required: true,
    },
    categoryListing: {
      type: Array,
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
    const dataList = 'categoryList';

    const formErrors = reactive({
      error: {
        internalName: {
          error: false,
          message: {
            de_DE: 'Eingabe fehlt!',
            en_EN: 'Value missing!',
          },
        },
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
      dataList,
      categoryForm,
      formErrors,
      toggleHint,
      checkInput,
    };
  },
});
</script>
