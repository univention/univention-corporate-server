<template>
  <div class="portal-button">
    <!-- button component -->
    <span
      role="button"
      aria-labelledby="DO_WE_USE_THAT"
      tabindex="0"
      style="user-select: none;"
    >
      <portal-icon
        v-if="iconBefore"
        :class="iconBeforeClass || iconBeforeClass"
        :icon="iconBefore"
        icon-width="2rem"
      />
      <span>
        <translate :i18n-key="buttonLabel" />
      </span>
      <portal-icon
        v-if="iconAfter"
        :class="iconAfterClass || iconAfterClass"
        :icon="iconAfter"
        icon-width="2rem"
      />
    </span>
    <input
      name="accept"
      type="button"
      value=""
      class="portal__off-screen"
      tabindex="-1"
      aria-hidden="true"
    >
    <!-- button component -->
  </div>
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';
import PortalIcon from '@/components/globals/PortalIcon.vue';
import Translate from '@/i18n/Translate.vue';

@Options({
  name: 'PortalButton',
  components: {
    PortalIcon,
    Translate,
  },
  props: {
    buttonLabel: {
      type: String,
      default: 'SUBMIT',
    },
    iconBefore: {
      type: String,
      default: '',
    },
    iconBeforeClass: {
      type: String,
      default: '',
    },
    iconAfter: {
      type: String,
      default: '',
    },
    iconAfterClass: {
      type: String,
      default: '',
    },
  },
  methods: {},
})
export default class PortalButton extends Vue {}
</script>

<style lang="stylus">
.portal-button
  user-select: none;
</style>
