<template>
  <img
    :src="imagePath"
    :class="defaultClass"
    :alt="altText"
  >
</template>

<script lang="ts">
import { defineComponent } from 'vue';

interface ImageComponentData {
  imagePath: string,
}

export default defineComponent({
  name: 'ImageComponent',
  props: {
    filePath: {
      type: String,
      default: '/img',
    },
    fileName: {
      type: String,
      default: 'default_nav_tab_icon.jpg',
    },
    fileType: {
      type: String,
      default: 'jpg',
    },
    altText: {
      type: String,
      default: 'Alternative Text',
    },
    defaultClass: {
      type: String,
      default: 'header-tab__logo',
    },
  },
  data(): ImageComponentData {
    return {
      imagePath: '',
    };
  },
  created() {
    this.imageUrl();
  },
  methods: {
    imageUrl(): void {
      this.imagePath = `./${this.filePath}/${this.fileName}`;
    },
  },
});
</script>

<style lang="stylus" />
