<!--
  SPDX-FileCopyrightText: 2021-2026 Univention GmbH
  SPDX-License-Identifier: AGPL-3.0-only
-->
<template>
  <input
    :id="forAttrOfLabel"
    ref="input"
    type="number"
    :name="name"
    :value="modelValue"
    :aria-invalid="invalid"
    :aria-describedby="invalidMessageId || null"
    data-test="number-spinner"
    @input="$emit('update:modelValue', $event.target.value)"
  >
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import _ from '@/jsHelper/translate';
import { isValid } from '@/jsHelper/forms';

export default defineComponent({
  name: 'NumberSpinner',
  props: {
    name: {
      type: String,
      required: true,
    },
    modelValue: {
      type: String,
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
        type: 'NumberSpinner',
        invalidMessage: this.invalidMessage,
      });
    },
  },
  methods: {
    focus() {
      (this.$refs.input as HTMLInputElement).focus();
    },
  },
});

</script>
