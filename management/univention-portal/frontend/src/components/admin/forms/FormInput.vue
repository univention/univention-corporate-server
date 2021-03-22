<template>
  <div class="form-input__wrapper">
    <label class="form-input__label">
      <!-- <translate :i18n-key="inputLabel" /> -->
      <span v-if="inputMandatory"> *</span>
    </label>
    <div
      class="form-input__container"
    >
      yyy - {{ formData }}
      <input
        v-model="formData"
        :type="inputType"
        :placeholder="placeHolder"
        :class="`form-input--default form-input--${inputType}`"
        :disabled="inputDisabled === true"
        autocomplete="off"
        tabindex="0"
        aria-required="true"
        aria-invalid="false"
      >
    </div>
  </div>
</template>

<script>
import { defineComponent, computed } from 'vue';

// import Translate from '@/i18n/Translate.vue';

export default defineComponent({
  name: 'FormInput',
  components: {
    // Translate,
  },
  props: {
    modelValue: {
      type: String,
      default: '',
    },
    inputLabel: {
      type: String,
      default: '',
    },
    inputName: {
      type: String,
      default: '',
    },
    inputType: {
      type: String,
      default: 'text',
    },
    inputValue: {
      type: String,
      default: '',
    },
    inputMandatory: {
      type: Boolean,
      default: false,
    },
    inputDisabled: {
      type: Boolean,
      default: false,
    },
    placeHolder: {
      type: String,
      default: 'text',
    },
  },
  emits: [
    'update:modelValue',
  ],
  setup(props, { emit }) {
    const formData = computed({
      get: () => props.inputValue,
      set: (value) => emit('update:inputValue', value),
    });

    return {
      formData,
    };
  },
  // methods: {
  //   emitValue(evt) {
  //     // const val = evt.target.value;

  //     // console.log('input: ', { evt, val });

  //     this.$emit('update:modelValue', evt);
  //   },
  // },
});
</script>

<style lang="stylus">
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
</style>
