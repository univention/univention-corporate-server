#!/bin/bash

function add_shadow {
	image="$1"
	convert "$image" \( +clone -background black -shadow 40x5+0+0 \) +swap -background white -layers merge +repage "$image"
}

unshadowed_images=(\
	installer-isolinux.png \
	installer-keyboardselection_*.png \
	installer-language.png \
	installer-location_*.png \
	installer-netcfg-dhcp_*.png \
	installer-netcfg-ip_*.png \
	installer-netcfg-static_*.png \
	installer-partman-selectguided_*.png \
	installer-partman-writelvm_*.png \
	installer-password_*.png \
)
shadowed_images=(\
	installer-domainrole_*.png \
	installer-hostname_*.png \
	installer-softwareselection_*.png \
	installer-overview_*.png \
)
all_images=(${unshadowed_images[*]} ${shadowed_images[*]})

for image in ${shadowed_images[*]}; do
	add_shadow $image
done

mkdir manual
mv ${all_images[*]} manual
