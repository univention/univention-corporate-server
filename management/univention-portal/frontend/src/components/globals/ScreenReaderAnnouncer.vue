<template>
  <div
    class="sr-only sr-only-mobile"
  >
    <div
      v-for="message in messages"
      :key="message.id"
    >
      <span
        :id="'sreen-reader-' + message.id"
        aria-live="assertive"
        aria-relevant="additions removals"
        aria-atomic="false"
      >
        {{ message.msg }}
      </span>
    </div>
  </div>
</template>
<script lang="ts">
import { defineComponent } from 'vue';
import { mapGetters } from 'vuex';

export default defineComponent({
  name: 'ScreenReaderAnnouncer',
  props: {
  },
  computed: {
    ...mapGetters({
      messages: 'activity/announce',
    }),
  },
});
</script>
