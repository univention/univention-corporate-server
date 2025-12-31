<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <form :id="id">
    <main>
      <form-element
        v-for="widget in widgets"
        :key="widget.name"
        :ref="widget.name"
        :widget="widget"
        :model-value="modelValue[widget.name]"
        @update:model-value="onUpdate(widget.name, $event)"
      />
    </main>
    <slot />
  </form>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';

import FormElement from '@/components/forms/FormElement.vue';
import { isValid, allValid, validateAll, WidgetDefinition } from '@/jsHelper/forms';

function isInteractable(widget) {
  return !(widget.readonly ?? false) && !(widget.disabled ?? false);
}

export default defineComponent({
  name: 'Form',
  components: {
    FormElement,
  },
  props: {
    id: {
      type: String,
      required: false,
    },
    modelValue: {
      // type: Object, TODO
      required: true,
    },
    widgets: {
      type: Array as PropType<WidgetDefinition[]>,
      required: true,
    },
  },
  emits: ['update:modelValue'],
  methods: {
    validate(): boolean {
      validateAll(this.widgets, this.modelValue);
      return allValid(this.widgets);
    },
    onUpdate(widgetName, value) {
      const newVal = JSON.parse(JSON.stringify(this.modelValue));
      newVal[widgetName] = value;
      this.$emit('update:modelValue', newVal);
    },
    focus(widgetName) {
      // @ts-ignore TODO
      this.$refs[widgetName].focus();
      // TODO focus only if interactable?
    },
    focusFirstInteractable() {
      // @ts-ignore TODO
      const first = this.widgets.find((widget) => isInteractable(widget));
      if (first) {
        this.focus(first.name);
      }
    },
    focusFirstInvalid() {
      // @ts-ignore TODO
      const first = this.widgets.find((widget) => isInteractable(widget) && !isValid(widget));
      if (first) {
        this.focus(first.name);
      }
    },
  },
});
</script>
