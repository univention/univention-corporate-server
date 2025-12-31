/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
export type ModalLevel = number | undefined;
export interface ModalProp {
  props?: {
    tiles?: Record<string, unknown>
  },
  level?: ModalLevel,
}

export interface ModalComponentInterface {
  level?:ModalLevel;
  name: string;
  props: ModalProp;
  stubborn: boolean;
  resolve: (any) => any;
  reject: () => any;
}
