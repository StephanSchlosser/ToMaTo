#!/bin/bash

if [ -f /etc/tomato/web.conf ]; then
  sed -i -e "s/XXX_REPLACE_ME_XXX/$(cat /dev/urandom | tr -dc _A-Z-a-z-0-9 | head -c33)/g" /etc/tomato/web.conf
fi