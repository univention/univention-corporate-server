<template>
  <div
    ref="modal"
    class="modal-admin__wrapper"
    role="dialog"
    aria-labelledby="TO_BE_SET"
    draggable="true"
  >
    <div
      :class="{ 'modal-admin__title-bar--draggable' : isMoveable }"
      class="modal-admin__title-bar"
      role="heading"
      level="1"
    >
      <span
        class="modal-admin__title"
        @mousedown="moveModal()"
      >
        <translate :i18n-key="modalTitle" />
      </span>

      <span
        v-if="showTitleButton"
        class="modal-admin__top-button--inner"
        role="presentation"
        @click="resetModal(), $emit('closeModal')"
      >
        <button
          ref="modal-title-button"
          aria-expanded="true"
          aria-label="Close modal"
          class="modal-admin__top-button"
        >
          <portal-icon
            icon="x"
            icon-width="2rem"
          />
        </button>
      </span>
    </div>

    <form>
      <div class="modal-admin__content">
        <template v-if="modalType === 'editCategory'">
          <form-category-edit
            v-model="categoryForm"
          />
          <pre v-if="modalDebugging">
            de: {{ categoryForm.title.de_DE }}
            en: {{ categoryForm.title.en_US }}
          </pre>
        </template>
        <template v-if="modalType === 'addNewCategory'">
          <form-category-add-new
            v-model="categoryForm"
          />
          <pre v-if="modalDebugging">
            dn: {{ categoryForm.internalName }}
            de: {{ categoryForm.title.de_DE }}
            en: {{ categoryForm.title.en_US }}
          </pre>
        </template>
      </div>

      <div class="modal-admin__footer">
        <span class="modal-admin__button">
          <button
            class="modal-admin__button--inner"
            @click="resetModal(), $emit('closeModal')"
          >
            <translate i18n-key="CANCEL" />
          </button>
        </span>

        <span
          v-if="removeAction"
          class="modal-admin__button"
        >
          <button
            class="modal-admin__button--inner"
            @click="resetModal(), $emit(removeAction)"
          >
            <translate i18n-key="REMOVE_FROM_PORTAL" />
          </button>
        </span>

        <span class="modal-admin__button">
          <button
            class="modal-admin__button--inner"
            @click.prevent="resetModal(), saveForm()"
          >
            <translate i18n-key="SAVE" />
          </button>
        </span>
      </div>
    </form>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, computed } from 'vue';
import { useStore } from 'vuex';

import PortalIcon from '@/components/globals/PortalIcon.vue';

// Forms
import FormCategoryEdit from '@/components/admin/forms/FormCategoryEdit.vue';
import FormCategoryAddNew from '@/components/admin/forms/FormCategoryAddNew.vue';

import Translate from '@/i18n/Translate.vue';

import moveContent from '@/jsHelper/moveContent';

export default defineComponent({
  name: 'ModalEditCategory',
  components: {
    PortalIcon,
    FormCategoryEdit,
    FormCategoryAddNew,
    Translate,
  },
  props: {
    variant: {
      type: String,
      required: true,
    },
    modalType: {
      type: String,
      default: 'add',
    },
    modalTitle: {
      type: String,
      required: true,
    },
    showTitleButton: {
      type: Boolean,
      default: true,
    },
    removeAction: {
      type: String,
      default: null,
    },
    saveAction: {
      type: String,
      required: true,
    },
    title: {
      type: Object,
      required: true,
    },
    categoryIndex: {
      type: Number,
      default: 0,
    },
    modalDebugging: {
      type: Boolean,
      default: false,
    },
  },
  emits: [
    'closeModal',
    'removeCategory',
    'saveCategory',
  ],
  setup(props, { emit }) {
    // vuex example: https://github.com/vuejs/vuex/blob/4.0/examples/composition/shopping-cart/components/ShoppingCart.vue
    const store = useStore();

    // data
    const modal = ref(null);
    const isMoveable = true;
    const showHint = ref(false);

    let categoryTitleDe = '';
    let categoryTitleEn = '';
    let internalNameValue = '';

    // get catgorie data for edit mode
    if (props.modalType === 'editCategory') {
      // TODO: keys have to be provided in the portal.json in parallel to the title

      const getPortalCategories = computed(() => store.getters['categories/getCategories']);

      const categoryTitle = getPortalCategories.value[props.categoryIndex];
      categoryTitleDe = categoryTitle.title.de_DE;
      categoryTitleEn = categoryTitle.title.en_US;

      const dn = getPortalCategories.value[props.categoryIndex].dn;
      internalNameValue = dn.substring(
        dn.indexOf('cn=') + 3,
        dn.indexOf(','),
      );
    }

    // v-model
    const categoryForm = reactive({
      key: {
        de_DE: 'de_DE',
        en_US: 'en_US',
      },
      title: {
        de_DE: categoryTitleDe,
        en_US: categoryTitleEn,
      },
      internalName: internalNameValue,
    });

    // methods
    const moveModal = () => {
      if (isMoveable) {
        moveContent(modal);
      }
    };

    const resetModal = () => {
      modal.value.style.top = '0';
      modal.value.style.left = '0';
    };

    const saveForm = () => {
      // console.log('saveForm: ', categoryForm);
      emit('saveCategory', categoryForm);
    };

    return {
      modal,
      isMoveable,
      showHint,
      categoryForm,
      moveModal,
      resetModal,
      saveForm,
    };
  },
});
</script>

<style lang="stylus">
.modal-admin
  &__wrapper
    background: var(--color-grey0)
    border-radius: 8px
    max-width: 650px
    box-shadow: var(--box-shadow)
    position: relative
    z-index: $zindex-5

  &__title-bar
    font-weight: bold
    padding: 2em 2em 1em 2em
    display: flex
    align-items: center

    &--draggable
      cursor: move

  &__title
    flex: 1 0 auto

  &__top-button
    width: 4rem
    height: 4rem
    background: none
    border: none
    color: white
    display: flex
    align-items: center
    justify-content: center
    background-color: transparent

    &:hover,
    &:focus
      border-radius: 100%
      background-color: var(--bgc-content-body)
      cursor: pointer

    &--inner
      margin-left: 1em
      cursor: pointer
      border: none
      border-radius: inherit
      display: flex
      align-items: center
      justify-content: center
      transition: var(--button-bgc-transition)
      background-color: var(--bgc-state)
      transition: opacity 250ms
      font-size: var(--button-font-size)

  &__content
    padding: 0 3em 1em 2em
  &__footer
    background-color: var(--color-grey0)
    display: flex
    justify-content: space-between
    border-top: thin solid var(--color-grey8)
    padding: 8px 24px
    flex-wrap: wrap

  &__hint
    position: absolute
    z-index: $zindex-6
    display: block
    overflow: visible
    padding-top: 0.5rem
    right: 2rem

  &__hint-icon
    margin-left: 1rem
    color: var(--font-color-disabled)
    width: 1.6rem
    &:hover
      cursor: pointer

  &__hint-connector
    position: absolute

  &__hint-content
    max-width: 400px
    font-size: 1.6rem
    color: var(--color-grey8)
    border-radius: var(--border-radius-tooltip)
    border: none
    padding: 0.6em 0.9em
    background: rgba(255,255,255,0.6)
    backdrop-filter: blur(20px)

  &__label
    color: var(--font-color-disabled)
    font-size: 1.6rem

  &__button
    background: none
    border: none
    display: flex
    align-items: center
    justify-content: center
    background-color: transparent
    &:first-of-type
      margin-left: 16px
    &:last-of-type
      margin-right: 16px

    &:hover,
    &:focus
      background-color: var(--bgc-content-body)
      cursor: pointer

    &--inner
      cursor: pointer
      border: none
      transition: var(--button-bgc-transition)
      background-color: var(--bgc-state)
      transition: opacity 250ms
      font-size: 16px
      color: #fff
      text-transform: uppercase
      padding: 16px

.form-input

  &__wrapper
    width: 100%
    min-width: 300px
    max-width: 650px
    padding: 0 0 3rem 0
    display: inline-block

  &__container
    width: 100%
    height: 58px

  &--error
    border: 1px solid var(--color-error) !important

  &--default
    width: 100%
    height: 100%
    color: var(--color)
    font-size: 2rem
    --bgc: var(--inputfield-bgc)
    background-color: var(--bgc)
    border: 1px solid var(--border-color)
    border-radius: var(--border-radius-interactable)
    padding: 0 1rem !important
    transition: background-color, color, border
    transition-duration: 250ms
    &:hover
      transition: background-color, color, border
      transition-duration: 250ms
    &:focus
      --border-color: var(--color-grey40)
      outline-style: none
      box-shadow: none
    &[disabled]
      cursor: var(--cursor-disabled)
      --color: var(--font-color-disabled)

  &--text
    height: 100%
    text-overflow: ellipsis

  &__label
    color: var(--font-color-disabled)
    font-size: 1.6rem
    &--error
      color: var(--color-error);

  &__icon
    &--error
      color: var(--color-error);
      position: relative
      top: 50px
      left: 78%

  &__error-message
    position: relative
    top: 1rem
    color: var(--color-error);
</style>
