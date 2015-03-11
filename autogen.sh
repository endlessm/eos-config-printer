#!/bin/sh
autoreconf --force -i

# Run configure unless requested not to.
if [ -z "$NOCONFIGURE" ]; then
    ./configure "$@"
fi
