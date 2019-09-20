//    Copyright 2016 Aurélien COUDERC <zecoucou@free.fr>
//
//    This program is free software: you can redistribute it and/or modify
//    it under the terms of the GNU General Public License as published by
//    the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.
//
//    This program is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU General Public License for more details.
//
//    You should have received a copy of the GNU General Public License
//    along with this program.  If not, see <https://www.gnu.org/licenses/>.

// This script is provided by desktop-base
// It is run by Plasma 5 on upgrade.
// Plasma checks that the script is only run once for each version.
d = desktops()

for (i in d) {
    // Only set up the wallpaper if the plugin is the default.
    // Otherwise it means the user chose another plugin and we don’t want to override that.
    if (d[i].wallpaperPlugin == 'org.kde.image') {
        d[i].currentConfigGroup = Array('Wallpaper', 'org.kde.image', 'General')
        if (!d[i].readConfig('Image')) {
            // Only set up the wallpaper if the wallpaper image is empty (=default).
            // Otherwise it means the user selected a picture and we don’t want to override that.
            d[i].writeConfig('Image', 'UCS-4.0');
        }
    }
}

