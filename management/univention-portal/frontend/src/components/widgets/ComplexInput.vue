<!--
 SPDX-License-Identifier: AGPL-3.0-only
 SPDX-FileCopyrightText: 2023-2024 Univention GmbH
-->

<template>
  <div
    class="complex-input"
    :class="{'complex-input__vertical' : isVertical}"
  >
    <form-element
      v-for="(widget, index) in widgets"
      :key="widget.name"
      :ref="`component-${widget.name}-${index}`"
      :widget="widget"
      :model-value="modelValue[index]"
      @update:modelValue="onUpdate(widget.name, $event, index)"
    />
    <input-error-message
      :display-condition="hasError"
      :error-message="getError"
    />
  </div>
</template>

<script lang="ts">
import { defineAsyncComponent, defineComponent, PropType } from 'vue';
import { WidgetDefinition } from '@/jsHelper/forms';
import InputErrorMessage from '@/components/forms/InputErrorMessage.vue';

export default defineComponent({
  name: 'ComplexInput',
  components: {
    FormElement: defineAsyncComponent(() => import('@/components/forms/FormElement.vue')),
    InputErrorMessage,
  },
  props: {
    modelValue: {
      type: Array,
      default: () => [],
      required: true,
    },
    subtypes: {
      type: Array as PropType<WidgetDefinition[]>,
      default: () => [],
      required: true,
    },
    name: {
      type: String,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
    required: {
      type: Boolean,
      default: false,
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
    direction: {
      type: String,
      default: 'horizontal',
    },
  },
  emits: ['update:modelValue'],
  computed: {
    widgets(): WidgetDefinition[] {
      this.subtypes.forEach((widget) => {
        widget.readonly = this.readonly;
        widget.required = this.required;
      });

      return this.subtypes;
    },
    hasError(): boolean {
      return this.getError !== '';
    },
    getError(): string {
      const error: any[] = [];
      this.subtypes.forEach((widget: WidgetDefinition) => {
        if (typeof widget.invalidMessage === 'string') {
          error.push(widget.invalidMessage);
        }
      });

      const message = this.invalidMessage.values;
      if (Array.isArray(message)) {
        error.push(...message);
      }

      return error
        .filter((item) => item)
        .join(' \r\n')
        .trim();
    },
    isVertical(): boolean {
      return this.direction === 'vertical';
    },
  },
  methods: {
    onUpdate(widgetName, value, index) {
      const newVal = JSON.parse(JSON.stringify(this.modelValue));
      newVal[index] = value;
      this.$emit('update:modelValue', newVal);
    },
  },
});
</script>

<style lang="stylus" scoped>
.complex-input
  display: flex
  flex-direction: column

  &__vertical
    flex-direction: row

    & > .form-element
      margin-right: 1rem

      &:last-child
        margin-right: 0
</style>
