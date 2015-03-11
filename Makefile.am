nobase_pkgdata_DATA = \
	config.py \
	debug.py \
	killtimer.py \
	pkgvalidator.py \
	utils.py

config.py: config.py.in Makefile
	sed \
	  -e "s|\@localstatedir\@|$(localstatedir)|" \
	  -e "s|\@LIBDIRNAME\@|$(LIBDIRNAME)|" \
	  -e "s|\@TMPDIRNAME\@|$(TMPDIRNAME)|" \
	  -e "s|\@PACKAGE\@|$(PACKAGE)|" \
	  $< > $@

EXTRA_DIST = \
	$(nobase_pkgdata_DATA) \
	autogen.sh \
	config.py.in \
	README.md \
	$(NULL)

CLEANFILES = \
	config.py \
	$(NULL)
