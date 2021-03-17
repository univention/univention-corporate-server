import { Module } from 'vuex';

export interface RootState {
  version: string;
}
export type PortalModule<S> = Module<S, RootState>;
