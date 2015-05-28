AC_INIT(eos-config-printer, 1.0.0)
AC_CONFIG_SRCDIR(eos-config-printer.py)
AM_INIT_AUTOMAKE([1.6 foreign])
AM_PATH_PYTHON([3])
AM_MAINTAINER_MODE([enable])

PACKAGE="AC_PACKAGE_NAME"
AC_SUBST(PACKAGE)

LIBDIRNAME=lib
PPDDIRNAME=ppd
TMPDIRNAME=tmp
AC_SUBST(LIBDIRNAME)
AC_SUBST(PPDDIRNAME)
AC_SUBST(TMPDIRNAME)

PKG_PROG_PKG_CONFIG

# For Polkit
PRINTERS_ADMIN_GROUP=lpadmin
AC_SUBST(PRINTERS_ADMIN_GROUP)

# For systemd
PKG_CHECK_EXISTS([systemd], [],
	[AC_MSG_ERROR([systemd required to build $PACKAGE_NAME])])

AC_ARG_WITH([systemdunitdir],
	[AS_HELP_STRING([--with-systemdunitdir],
			[systemd unit file directory])],
	[systemdunitdir=$withval],
	[systemdunitdir=`$PKG_CONFIG --variable=systemdsystemunitdir systemd`])
AS_IF([test "x$systemdunitdir" = x],
	[AC_MSG_ERROR([no path for systemd unit directory])])
AC_SUBST([systemdunitdir])

AC_CONFIG_FILES([
Makefile
data/eos-config-printer
])
AC_OUTPUT
