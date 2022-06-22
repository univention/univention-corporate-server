<template>
  <div
    class="multi-input"
  >
    <div
      v-for="(val, valIdx) in modelValue"
      :key="valIdx"
      :class="[
        'multi-input__row',
        {
          'multi-input__row--multiline': subtypes.length > 1,
          'multi-input__row--singleline': subtypes.length === 1,
          'multi-input__row--invalid': rowInvalidMessage(valIdx) !== '',
        },
      ]"
      data-test="multi-input-row"
    >
      <div
        v-for="(type, typeIdx) in subtypes"
        :key="typeIdx"
        class="multi-input__row__elem"
      >
        <form-element
          :ref="`component-${valIdx}-${typeIdx}`"
          :widget="getSubtypeWidget(type, valIdx, typeIdx)"
          :model-value="Array.isArray(val) ? val[typeIdx] : val"
          :data-test="`form-element-${getSubtypeWidget(type, valIdx, typeIdx).type}-${valIdx}`"
          @update:model-value="onUpdate(valIdx, typeIdx, $event)"
        />
      </div>
      <icon-button
        icon="trash"
        :tabindex="tabindex"
        :has-button-style="true"
        :aria-label-prop="REMOVE_BUTTON_LABEL(valIdx)"
        :data-test="`multi-input-remove-entry-button-${valIdx}`"
        @click="removeEntry(valIdx)"
      />
      <input-error-message
        :display-condition="rowInvalidMessage(valIdx) !== ''"
        :error-message="rowInvalidMessage(valIdx)"
      />
    </div>
    <icon-button
      icon="plus"
      :tabindex="tabindex"
      :has-button-style="true"
      :aria-label-prop="addButtonLabel"
      data-test="multi-input-add-entry-button"
      @click="addEntry()"
    />
  </div>
</template>

<script lang="ts">
// TODO handling of 'name' attribute
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';

import IconButton from '@/components/globals/IconButton.vue';
import InputErrorMessage from '@/components/forms/InputErrorMessage.vue';

import ComboBox from '@/components/widgets/ComboBox.vue';
import DateBox from '@/components/widgets/DateBox.vue';
import PasswordBox from '@/components/widgets/PasswordBox.vue';
import TextBox from '@/components/widgets/TextBox.vue';
import FormElement from '@/components/forms/FormElementCopyNeededForMultiInput.vue';
import { initialValue } from '@/jsHelper/forms';

export default defineComponent({
  name: 'MultiInput',
  components: {
    InputErrorMessage,
    // break circular dependency
    // FormElement: defineAsyncComponent(() => import('@/components/forms/FormElement.vue')),
    // TODO look for better solution
    // When loading FormElement as asynccomponent then ref="" is not immediately set (which is needed for focus).
    // For now we copy @/components/forms/FormElement.vue to @/components/forms/FormElement2.vue
    FormElement,
    IconButton,
    ComboBox,
    DateBox,
    PasswordBox,
    TextBox,
  },
  props: {
    modelValue: {
      type: Array,
      required: true,
    },
    subtypes: {
      type: Array,
      required: true,
    },
    extraLabel: {
      type: String,
      required: true,
    },
    invalidMessage: {
      type: Object,
      default() {
        return {
          all: '',
          values: [],
        };
      },
    },
    tabindex: {
      type: Number,
      default: 0,
    },
  },
  emits: ['update:modelValue'],
  computed: {
    addButtonLabel(): string {
      return _('Add new %(label)s', {
        label: this.extraLabel,
      });
    },
  },
  methods: {
    onUpdate(valIdx, typeIdx, val): void {
      const newVal = JSON.parse(JSON.stringify(this.modelValue));
      if (this.subtypes.length === 1) {
        newVal[valIdx] = val;
      } else {
        newVal[valIdx][typeIdx] = val;
      }
      this.$emit('update:modelValue', newVal);
    },
    addEntry(): void {
      const newVal = JSON.parse(JSON.stringify(this.modelValue));
      newVal.push(this.newRow());
      this.$emit('update:modelValue', newVal);
      this.$store.dispatch('activity/setMessage', _('%(label)s %(idx)s added', {
        label: this.extraLabel,
        idx: newVal.length,
      }));
      this.focusLastInputField();
    },
    newRow(): any {
      return initialValue({
        type: 'MultiInput',
        subtypes: this.subtypes,
      }, null)[0];
    },
    removeEntry(valIdx): void {
      const newVal = JSON.parse(JSON.stringify(this.modelValue));
      newVal.splice(valIdx, 1);
      if (newVal.length === 0) {
        newVal.push(this.newRow());
      }
      this.$emit('update:modelValue', newVal);
      this.$store.dispatch('activity/setMessage', _('%(label)s %(idx)s removed', {
        label: this.extraLabel,
        idx: valIdx + 1,
      }));
    },
    rowInvalidMessage(valIdx): string {
      // show invalidMessage for row only if we have multiple subtypes
      if (this.subtypes.length === 1) {
        return '';
      }
      const message = this.invalidMessage.values[valIdx];
      if (Array.isArray(message)) {
        return '';
      }
      return message ?? '';
    },
    getSubtypeWidget(type, valIdx, typeIdx): Record<any, any> {
      let message = this.invalidMessage.values[valIdx];
      if (Array.isArray(message)) {
        message = message[typeIdx];
      } else if (this.subtypes.length > 1) {
        message = '';
      }

      let labelScreenReader = `${this.extraLabel} ${valIdx + 1}`;
      if (type.label !== undefined && type.label !== this.extraLabel) {
        labelScreenReader += `: ${type.label}`;
      }
      return {
        ...type,
        tabindex: this.tabindex,
        ariaLabel: labelScreenReader,
        invalidMessage: message ?? '',
      };
    },
    focus(): void {
      const firstWidget = this.$refs['component-0-0'];
      // TODO find first interactable?
      if (firstWidget) {
        (firstWidget as HTMLElement).focus();
      }
    },
    REMOVE_BUTTON_LABEL(idx): string {
      return _('Remove %(label)s %(idx)s', {
        label: this.extraLabel,
        idx: idx + 1,
      });
    },
    focusLastInputField(): void {
      // MultiInput can have multiple widgets per row.
      // Focus first widget in last row.

      // @ts-ignore FIXME not sure how to fix this error
      this.$nextTick(() => {
        const firstRowEntryRefs = Object.keys(this.$refs)
          .filter((ref) => {
            // Filter out widgets that are not the first of their row.
            const column = ref.split('-')[2];
            try {
              return parseInt(column, 10) === 0;
            } catch (e) {
              return true;
            }
          })
          .sort();
        const lastItemRef = firstRowEntryRefs[firstRowEntryRefs.length - 1];
        (this.$refs[lastItemRef] as HTMLElement).focus();
      });
    },
  },
});
</script>

<style lang="stylus">
$groupingStyle
  --local-stripeColor: var(--bgc-inputfield-on-container)
  padding-top: var(--layout-spacing-unit-small)
  padding-left: var(--layout-spacing-unit)
  margin-left: 2px
  box-shadow: inset 2px 0 var(--local-stripeColor)

.multi-input__row
  label
    margin-top: 0

  &--singleline
    display: flex
    align-items: flex-start
    gap: var(--layout-spacing-unit)
    margin-bottom: calc(1 * var(--layout-spacing-unit))

    label
      position: absolute
      width: 1px
      height: 1px
      padding: 0
      margin: -1px
      overflow: hidden
      clip: rect(0,0,0,0)
      border: 0

    .icon-button
      flex: 0 0 auto

    .multi-input__row__elem
      flex: 1 1 auto

  &--multiline
    @extends $groupingStyle
    display: flex
    flex-direction: column
    margin-bottom: calc(2 * var(--layout-spacing-unit))
    .multi-input__row__elem
      margin-bottom: var(--layout-spacing-unit)
  &--invalid
    --local-stripeColor: var(--font-color-error)

.multi-input__row__elem .form-element
  margin-top: 0
</style>
