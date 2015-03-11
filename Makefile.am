bin_SCRIPTS = data/eos-config-printer

nobase_pkgdata_SCRIPTS = eos-config-printer.py

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
	  -e "s|\@PPDDIRNAME\@|$(PPDDIRNAME)|" \
	  -e "s|\@TMPDIRNAME\@|$(TMPDIRNAME)|" \
	  -e "s|\@PACKAGE\@|$(PACKAGE)|" \
	  $< > $@

EXTRA_DIST = \
	$(bin_SCRIPTS) \
	$(nobase_pkgdata_SCRIPTS) \
	$(nobase_pkgdata_DATA) \
	autogen.sh \
	config.py.in \
	README.md \
	$(NULL)

CLEANFILES = \
	config.py \
	$(NULL)
