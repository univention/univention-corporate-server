/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

export interface User {
    username: string;
    displayName: string;
    mayEditPortal: boolean;
    authMode: string;
}

export interface UserWrapper {
    user: User
}
