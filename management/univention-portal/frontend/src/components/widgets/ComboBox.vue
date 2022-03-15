<template>
  <select
    :id="forAttrOfLabel"
    ref="select"
    :name="name"
    :value="modelValue"
    :aria-invalid="invalid"
    :aria-describedby="invalidMessageId || null"
    data-test="combo-box"
    @change="$emit('update:modelValue', $event.target.value)"
  >
    <option
      v-for="option in options"
      :key="option.id"
      :value="option.id"
    >
      {{ option.label }}
    </option>
  </select>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { isValid } from '@/jsHelper/forms';

export default defineComponent({
  name: 'ComboBox',
  props: {
    name: {
      type: String,
      required: true,
    },
    modelValue: {
      type: String,
      required: true,
    },
    options: {
      type: Array,
      required: true,
    },
    invalidMessage: {
      type: String,
      default: '',
    },
    forAttrOfLabel: {
      type: String,
      required: true,
    },
    invalidMessageId: {
      type: String,
      required: true,
    },
  },
  emits: ['update:modelValue'],
  computed: {
    invalid(): boolean {
      return !isValid({
        type: 'ComboBox',
        invalidMessage: this.invalidMessage,
      });
    },
  },
  methods: {
    focus() {
      // @ts-ignore
      this.$refs.select.focus();
    },
  },
});
</script>
