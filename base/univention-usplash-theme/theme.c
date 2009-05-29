/* usplash
 *
 * eft-theme.c - definition of eft theme
 *
 * Copyright © 2006 Dennis Kaarsemaker <dennis@kaarsemaker.net>
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
 */

#include <usplash-theme.h>
/* Needed for the custom drawing functions */
#include <usplash_backend.h>

#define BACKGROUND 0
#define PROGRESSBAR_BACKGROUND 25
#define PROGRESSBAR_FOREGROUND 15
#define TEXT_BACKGROUND 25
#define TEXT_FOREGROUND 3
#define TEXT_SUCCESS 185
#define TEXT_FAILURE 111

#define PROGRESSBAR_WIDTH 350
#define PROGRESSBAR_HEIGHT 8

extern struct usplash_pixmap pixmap_silent_splash_640x480, pixmap_silent_splash_800x600, pixmap_silent_splash_1024x768, pixmap_silent_splash_1280x1024, pixmap_silent_splash_1600x1200;
extern struct usplash_pixmap pixmap_throbber_back;
extern struct usplash_pixmap pixmap_throbber_fore;
extern struct usplash_font font_helvB10;

void t_init(struct usplash_theme* theme);
void t_clear_progressbar(struct usplash_theme* theme);
void t_draw_progressbar(struct usplash_theme* theme, int percentage);
void t_animate_step(struct usplash_theme* theme, int pulsating);

struct usplash_theme usplash_theme;
struct usplash_theme usplash_theme_800_600;
struct usplash_theme usplash_theme_1024_768;
struct usplash_theme usplash_theme_1280_1024;
struct usplash_theme usplash_theme_1600_1200;

/* Theme definition */
struct usplash_theme usplash_theme = {
	.version = THEME_VERSION, /* ALWAYS set this to THEME_VERSION, 
                                 it's a compatibility check */
    .next = &usplash_theme_800_600,
    .ratio = USPLASH_4_3,

	/* Background and font */
	.pixmap = &pixmap_silent_splash_640x480,
	.font   = &font_helvB10,

	/* Palette indexes */
	.background             = BACKGROUND,
  	.progressbar_background = PROGRESSBAR_BACKGROUND,
  	.progressbar_foreground = PROGRESSBAR_FOREGROUND,
	.text_background        = TEXT_BACKGROUND,
	.text_foreground        = TEXT_FOREGROUND,
	.text_success           = TEXT_SUCCESS,
	.text_failure           = TEXT_FAILURE,

	/* Progress bar position and size in pixels */
  	.progressbar_x      = 640/2 - PROGRESSBAR_WIDTH/2,
  	.progressbar_y      = 371,
  	.progressbar_width  = PROGRESSBAR_WIDTH,
  	.progressbar_height = PROGRESSBAR_HEIGHT,

	/* Text box position and size in pixels */
  	.text_x      = 120,
  	.text_y      = 307,
  	.text_width  = 360,
  	.text_height = 100,

	/* Text details */
  	.line_height  = 15,
  	.line_length  = 32,
  	.status_width = 35,

    /* Functions */
    .init = t_init,
    .clear_progressbar = t_clear_progressbar,
    .draw_progressbar = t_draw_progressbar,
    .animate_step = t_animate_step,
};


/* Theme definition */
struct usplash_theme usplash_theme_800_600 = {
	.version = THEME_VERSION, /* ALWAYS set this to THEME_VERSION, 
                                 it's a compatibility check */
    .next = &usplash_theme_1024_768,
    .ratio = USPLASH_4_3,

	/* Background and font */
	.pixmap = &pixmap_silent_splash_800x600,
	.font   = &font_helvB10,

	/* Palette indexes */
	.background             = BACKGROUND,
  	.progressbar_background = PROGRESSBAR_BACKGROUND,
  	.progressbar_foreground = PROGRESSBAR_FOREGROUND,
	.text_background        = TEXT_BACKGROUND,
	.text_foreground        = TEXT_FOREGROUND,
	.text_success           = TEXT_SUCCESS,
	.text_failure           = TEXT_FAILURE,

	/* Progress bar position and size in pixels */
  	.progressbar_x      = 800/2 - PROGRESSBAR_WIDTH/2,
  	.progressbar_y      = 371,
  	.progressbar_width  = PROGRESSBAR_WIDTH,
  	.progressbar_height = PROGRESSBAR_HEIGHT,

	/* Text box position and size in pixels */
  	.text_x      = 120,
  	.text_y      = 307,
  	.text_width  = 360,
  	.text_height = 100,

	/* Text details */
  	.line_height  = 15,
  	.line_length  = 32,
  	.status_width = 35,

    /* Functions */
    .init = t_init,
    .clear_progressbar = t_clear_progressbar,
    .draw_progressbar = t_draw_progressbar,
    .animate_step = t_animate_step,
};

struct usplash_theme usplash_theme_1024_768 = {
	.version = THEME_VERSION,
    .next = &usplash_theme_1280_1024,
    .ratio = USPLASH_4_3,

	/* Background and font */
	.pixmap = &pixmap_silent_splash_1024x768,
	.font   = &font_helvB10,

	/* Palette indexes */
	.background             = BACKGROUND,
  	.progressbar_background = PROGRESSBAR_BACKGROUND,
  	.progressbar_foreground = PROGRESSBAR_FOREGROUND,
	.text_background        = TEXT_BACKGROUND,
	.text_foreground        = TEXT_FOREGROUND,
	.text_success           = TEXT_SUCCESS,
	.text_failure           = TEXT_FAILURE,

	/* Progress bar position and size in pixels */
  	/*.progressbar_x      = 404,  1024/2 - 216/2 */
  	.progressbar_x      = 1024/2 - PROGRESSBAR_WIDTH/2,
  	.progressbar_y      = 475,
  	.progressbar_width  = PROGRESSBAR_WIDTH,
  	.progressbar_height = PROGRESSBAR_HEIGHT,

	/* Text box position and size in pixels */
  	.text_x      = 322,
  	.text_y      = 525,
  	.text_width  = 380,
  	.text_height = 100,

	/* Text details */
  	.line_height  = 15,
  	.line_length  = 32,
  	.status_width = 35,

    /* Functions */
    .init = t_init,
    .clear_progressbar = t_clear_progressbar,
    .draw_progressbar = t_draw_progressbar,
    .animate_step = t_animate_step,
};

struct usplash_theme usplash_theme_1280_1024 = {
	.version = THEME_VERSION,
    .next = NULL,
    .ratio = USPLASH_4_3,

	/* Background and font */
	.pixmap = &pixmap_silent_splash_1280x1024,
	.font   = &font_helvB10,

	/* Palette indexes */
	.background             = BACKGROUND,
  	.progressbar_background = PROGRESSBAR_BACKGROUND,
  	.progressbar_foreground = PROGRESSBAR_FOREGROUND,
	.text_background        = TEXT_BACKGROUND,
	.text_foreground        = TEXT_FOREGROUND,
	.text_success           = TEXT_SUCCESS,
	.text_failure           = TEXT_FAILURE,

	/* Progress bar position and size in pixels */
  	.progressbar_x      = 1240/2 - PROGRESSBAR_WIDTH/2,
  	.progressbar_y      = 475,
  	.progressbar_width  = PROGRESSBAR_WIDTH,
  	.progressbar_height = PROGRESSBAR_HEIGHT,

	/* Text box position and size in pixels */
  	.text_x      = 322,
  	.text_y      = 525,
  	.text_width  = 380,
  	.text_height = 100,

	/* Text details */
  	.line_height  = 15,
  	.line_length  = 32,
  	.status_width = 35,

    /* Functions */
    .init = t_init,
    .clear_progressbar = t_clear_progressbar,
    .draw_progressbar = t_draw_progressbar,
    .animate_step = t_animate_step,
};
void t_init(struct usplash_theme *theme) {
    int x, y;
    usplash_getdimensions(&x, &y);
    theme->progressbar_x = (x - theme->pixmap->width)/2 + theme->progressbar_x;
    theme->progressbar_y = (y - theme->pixmap->height)/2 + theme->progressbar_y;
}

void t_clear_progressbar(struct usplash_theme *theme) {
    t_draw_progressbar(theme, 0);
}

void t_draw_progressbar(struct usplash_theme *theme, int percentage) {
    int w = (pixmap_throbber_back.width * percentage / 100);
    usplash_put(theme->progressbar_x, theme->progressbar_y, &pixmap_throbber_back);
    if(percentage == 0)
        return;
    if(percentage < 0)
        usplash_put_part(theme->progressbar_x - w, theme->progressbar_y, pixmap_throbber_back.width + w,
                         pixmap_throbber_back.height, &pixmap_throbber_fore, -w, 0);
    else
        usplash_put_part(theme->progressbar_x, theme->progressbar_y, w, pixmap_throbber_back.height, 
                         &pixmap_throbber_fore, 0, 0);
}

void t_animate_step(struct usplash_theme* theme, int pulsating) {

    static int pulsate_step = 0;
    static int pulse_width = 28;
    static int step_width = 2;
    static int num_steps = (PROGRESSBAR_WIDTH - 28 - 2)/2;
    int x1;

    if (pulsating) {
        t_draw_progressbar(theme, 0);
    
        if(pulsate_step < num_steps/2+1)
	        x1 = 2 * step_width * pulsate_step;
        else
	        x1 = PROGRESSBAR_WIDTH - pulse_width - 2 * step_width * (pulsate_step - num_steps/2+1);

        usplash_put_part(theme->progressbar_x + x1, theme->progressbar_y, pulse_width,
                         pixmap_throbber_fore.height, &pixmap_throbber_fore, x1, 0);

        pulsate_step = (pulsate_step + 1) % num_steps;
    }
}
