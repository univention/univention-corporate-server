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
    border-radius: var(--border-radius-container)
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
    color: var(--color-grey8)
    border-radius: var(--border-radius-tooltip)
    border: none
    padding: 0.6em 0.9em
    background: rgba(255,255,255,0.6)
    backdrop-filter: blur(20px)

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
      color: #fff
      text-transform: uppercase
      padding: 16px

.form-input

  &__wrapper
    width: 100%
    display: inline-block

  &__container
    width: 100%

  &--error
    border: 1px solid var(--color-error) !important

  &--text
    text-overflow: ellipsis

  &__icon
    &--error
      display: none
      color: var(--color-error);
      position: relative
      top: 50px
      left: 78%

  &__error-message
    position: relative
    top: 1rem
    color: var(--color-error);
</style>
