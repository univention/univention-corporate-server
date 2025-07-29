/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

export default function tabindex(activeAt: string[], activityLevel: string): number {
  if (activeAt.indexOf(activityLevel) > -1) {
    return 0;
  }
  return -1;
}
