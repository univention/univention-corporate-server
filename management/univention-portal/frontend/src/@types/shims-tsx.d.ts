declare global {
  // allow the use of .tsx files while enabling jsx syntaxsupport in your IDE to write JSX-style typescript code
  import Vue, { VNode } from 'vue';

  /* eslint-disable no-unused-vars */
  namespace JSX {
    interface Element extends VNode {}
    interface ElementClass extends Vue {}
    interface IntrinsicElements {
      [elem: string]: unknown;
    }
  }
  /* eslint-enable no-unused-vars */
}
