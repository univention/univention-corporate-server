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
    class="dialog"
    @keydown.esc="cancel()"
  >
    <header class="dialog__header">
      <h3>
        <translate
          v-if="i18nTitleKey"
          :i18n-key="i18nTitleKey"
        />
        <span v-else>
          {{ title }}
        </span>
      </h3>
      <icon-button
        v-if="cancelAllowed"
        icon="x"
        :active-at="['modal']"
        :aria-label-prop="ariaLabelCancel"
        @click="cancel()"
      />
    </header>
    <slot />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import Translate from '@/i18n/Translate.vue';
import IconButton from '@/components/globals/IconButton.vue';

export default defineComponent({
  name: 'ModalDialog',
  components: {
    Translate,
    IconButton,
  },
  props: {
    i18nTitleKey: {
      type: String,
      default: '',
    },
    title: {
      type: String,
      default: '',
    },
    cancelAllowed: {
      type: Boolean,
      required: false,
      default: true,
    },
  },
  emits: ['cancel'],
  computed: {
    ariaLabelCancel(): string {
      return this.$translateLabel('CANCEL');
    },
  },
  methods: {
    cancel(): void {
      if (this.cancelAllowed) {
        this.$emit('cancel');
      }
    },
  },
});
</script>

<style lang="stylus">
.dialog
  padding: calc(2 * var(--layout-spacing-unit)) calc(4 * var(--layout-spacing-unit))
  background: var(--bgc-content-container)
  border-radius: var(--border-radius-container)
  max-width: calc(50 * var(--layout-spacing-unit))
  box-shadow: var(--box-shadow)

  form
    width: calc(var(--inputfield-width) + 3rem)

  main
    max-height: 26rem
    overflow: auto
    padding-right: var(--layout-spacing-unit)

    > label:first-child
      margin-top: 0

  footer:not(.image-upload__footer)
    margin-top: calc(2 * var(--layout-spacing-unit))
    padding-top: calc(2 * var(--layout-spacing-unit))
    border-top: thin solid var(--bgc-tab-separator)
    /* padding: var(--layout-spacing-unit-small) calc(2 * var(--layout-spacing-unit))*/
    display: flex
    justify-content: space-between
    flex-wrap: wrap

    button:last-of-type
      margin-left: auto

  &__header
    display: flex
    align-items: center

    button
      margin-left: auto
</style>
