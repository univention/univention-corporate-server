<!--
  Copyright 2021-2022 Univention GmbH

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
    :class="[
      'form-element',
      { 'form-element--invalid': invalid },
      `form-element--${widget.type}`
    ]"
    data-test="form-element"
  >
    <form-label
      :label="widget.label"
      :aria-label="widget.ariaLabel || widget.label"
      :required="widget.required"
      :for-attr="forAttrOfLabel"
      :invalid-message="invalidMessage"
      :show-help-icon="hasDescription"
      data-test="form-element-label"
      :display-description="displayDescription"
      @toggle-description="toggleDescription"
    />
    <!-- <div class="form-element__wrapper"> -->
    <Transition>
      <p
        v-if="displayDescription"
        class="form-element__help-text"
      >
        {{ widget.description }}
      </p>
    </Transition>
    <component
      :is="widget.type"
      ref="component"
      v-bind="component"
      :model-value="modelValue"
      :for-attr-of-label="forAttrOfLabel"
      data-test="form-element-component"
      :invalid-message-id="invalidMessageId"
      @update:model-value="$emit('update:modelValue', $event)"
    />
    <input-error-message
      :id="invalidMessageId"
      :display-condition="invalidMessage !== ''"
      :error-message="invalidMessage"
    />
    <!-- </div> -->
  </div>
</template>

<script lang="ts">
import { defineComponent, PropType } from 'vue';
import FormLabel from '@/components/forms/FormLabel.vue';
import InputErrorMessage from '@/components/forms/InputErrorMessage.vue';
import { isValid, invalidMessage, WidgetDefinition } from '@/jsHelper/forms';

// TODO load components on demand (?)
import ComboBox from '@/components/widgets/ComboBox.vue';
import DateBox from '@/components/widgets/DateBox.vue';
import MultiInput from '@/components/widgets/MultiInput.vue';
import PasswordBox from '@/components/widgets/PasswordBox.vue';
import TextBox from '@/components/widgets/TextBox.vue';
import TextArea from '@/components/widgets/TextArea.vue';
import CheckBox from '@/components/widgets/CheckBox.vue';
import RadioBox from '@/components/widgets/RadioBox.vue';
import ImageUploader from '@/components/widgets/ImageUploader.vue';
import LocaleInput from '@/components/widgets/LocaleInput.vue';
import MultiSelect from '@/components/widgets/MultiSelect.vue';
import LinkWidget from '@/components/widgets/LinkWidget.vue';
import NumberSpinner from '@/components/widgets/NumberSpinner.vue';
import TimeBox from '@/components/widgets/TimeBox.vue';

export default defineComponent({
  name: 'FormElement',
  components: {
    FormLabel,
    InputErrorMessage,
    ComboBox,
    DateBox,
    MultiInput,
    PasswordBox,
    TextBox,
    CheckBox,
    RadioBox,
    ImageUploader,
    LocaleInput,
    MultiSelect,
    LinkWidget,
    TextArea,
    NumberSpinner,
    TimeBox,
  },
  props: {
    widget: {
      type: Object as PropType<WidgetDefinition>,
      required: true,
    },
    modelValue: {
      required: true,
    },
  },
  emits: ['update:modelValue'],
  data() {
    return {
      displayDescription: false,
    };
  },
  computed: {
    component(): any {
      const component = JSON.parse(JSON.stringify(this.widget));
      delete component.type;
      delete component.label;
      delete component.ariaLabel;
      delete component.validators;
      return component;
    },
    invalid(): boolean {
      return !isValid(this.widget);
    },
    invalidMessage(): string {
      return invalidMessage(this.widget);
    },
    forAttrOfLabel(): string {
      return `${this.widget.name}--${this.$.uid}`;
    },
    invalidMessageId(): string {
      return this.invalidMessage !== '' ? `${this.forAttrOfLabel}--error` : '';
    },
    hasDescription(): boolean {
      if (this.widget.description === undefined) {
        return false;
      }
      return this.widget.description.length > 0;
    },
  },
  methods: {
    focus() {
      // @ts-ignore TODO
      this.$refs.component.focus();
    },
    toggleDescription() {
      this.displayDescription = !this.displayDescription;
    },
  },
});
</script>

<style lang="stylus">
.form-element
  margin-top: calc(3 * var(--layout-spacing-unit))

  input,
  select,
  label
    margin: 0

  .input-error-message
    margin: 0
    margin-top: var(--layout-spacing-unit)

  &--CheckBox
    display: grid
    grid-template-columns: auto 1fr
    grid-template-rows: auto auto
    grid-template-areas: "checkbox label" "invalidMessage invalidMessage"

    input
      grid-area: checkbox
    label
      grid-area: label
    .input-error-message
      grid-area: invalidMessage

  &__help-text
    margin-top: 0
    font-size: var(--font-size-5)
    color: var(--font-color-contrast-middle)

.v-enter-active,
.v-leave-active {
  transition: opacity 0.25s ease;
}

.v-enter-from,
.v-leave-to {
  opacity: 0;
}
  /*
  &--invalid
    > .form-element__wrapper
      padding-left: var(--layout-spacing-unit)
      margin-left: 2px
      box-shadow: inset 2px 0 var(--font-color-error)
   */
</style>
