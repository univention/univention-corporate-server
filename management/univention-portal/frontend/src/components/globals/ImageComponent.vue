<template>
  <img
    :src="imagePath"
    :class="defaultClass"
    :alt="altText"
  >
</template>

<script lang="ts">
import { Options, Vue } from 'vue-class-component';

@Options({
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
  data() {
    return {
      imagePath: '',
    };
  },
  created() {
    this.imageUrl();
  },
  methods: {
    imageUrl() {
      this.imagePath = `./${this.filePath}/${this.fileName}`;
    },
  },
})

export default class ImageComponent extends Vue {}
</script>

<style lang="stylus">

</style>
