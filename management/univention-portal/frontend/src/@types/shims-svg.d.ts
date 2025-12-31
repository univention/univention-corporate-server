/*
 * SPDX-FileCopyrightText: 2021-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
declare module '*.svg' {
  // It's really a string, precisely a resolved path pointing to the image file
  const filePath: string;

  export default filePath;
}
