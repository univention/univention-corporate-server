import { store } from '@/store/';

declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $store: store;
  }
}
