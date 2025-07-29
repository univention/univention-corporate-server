/*
 * SPDX-FileCopyrightText: 2021-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

export interface Tooltip {
    title: string | null,
    icon: string | null,
    backgroundColor: string | null,
    description: string,
    ariaId: string,
    position: Record<string, number>,
    isMobile: boolean | null,
    linkType: string | null,
}
