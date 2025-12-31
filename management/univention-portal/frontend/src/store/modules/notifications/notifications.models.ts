/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

export interface Notification {
  title: string;
  description?: string;
  onClick: () => void | null;
}

export interface WeightedNotification extends Notification {
  hidingAfter: number;
  importance: string;
}

export interface FullNotification extends WeightedNotification {
  visible: boolean;
  token: number;
}
