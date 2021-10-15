<template>
  <main class="portal-error">
    <h1> {{ ERROR_MESSAGE }} </h1>
    <p> {{ ERROR_SUBTEXT }} </p>
  </main>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';
import _ from '@/jsHelper/translate';

export default defineComponent({
  name: 'Portalerror',
  computed: {
    ...mapGetters({
      errorContentType: 'portalData/errorContentType',
    }),
    ERROR_MESSAGE(): string {
      return _('Sorry.');
    },
    ERROR_SUBTEXT(): string {
      return _('The portal is temporarily unavailable. If the problem persists, please contact your system administrator.');
    },
  },
});
</script>
<style lang="stylus">
.portal-error
  position: relative
  display: flex
  flex-direction: column
  margin-left: 5em

  @media $mqSmartphone
    margin-left: 1em
</style>
