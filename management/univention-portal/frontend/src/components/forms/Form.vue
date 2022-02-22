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
  <form>
    <form-element
      v-for="widget in widgets"
      :key="widget.name"
      :ref="widget.name"
      :widget="widget"
      :model-value="modelValue[widget.name]"
      @update:model-value="onUpdate(widget.name, $event)"
    />
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
