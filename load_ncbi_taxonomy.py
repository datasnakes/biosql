#!/usr/bin/python3 -w
#
# $Id$
#
# Copyright 2017 Rob Gilmore
#
#  This file is part of BioSQL.
#
#  BioSQL is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  BioSQL is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with BioSQL. If not, see <http://www.gnu.org/licenses/>.

"""

load_ncbi_taxonomy.pl

=head1 SYNOPSIS

Usage: load_ncbi_taxonomy.pl
--dbname     # name of database to use
--dsn        # the DSN of the database to connect to
--driver     # "mysql", "Pg", "Oracle", "SQLite" (default "mysql")
--host       # optional: host to connect with
--port       # optional: port to connect with
--dbuser     # optional: user name to connect with
--dbpass     # optional: password to connect with
--download   # optional: whether to download new NCBI taxonomy data
--directory  # optional: where to store/look for the data
--schema     # optional: Pg only, load using given schema

=head1 DESCRIPTION

This script loads or updates a biosql schema with the NCBI Taxon
Database. There are a number of options to do with where the biosql
database is (i.e., database name, hostname, user for database,
                                                     password, database name).

This script may download the NCBI Taxon Database from the NCBI FTP
server on-the-fly (ftp://ftp.ncbi.nih.gov/pub/taxonomy/). Otherwise it
expects the files to be downloaded already.

You can use this script to load taxon data into a fresh instance of
biosql, or to update the taxon content of an already populated biosql
database. Because it updates taxon nodes rather than dumping and
re-inserting them, bioentries referencing those existing taxon nodes
are unaffected. An update will erase all changes you made on taxon
nodes and their names which have an NCBI TaxonID set. Names of nodes
that do not have an NCBI TaxonID will be left untouched.

Note that we used to have the convention to re-use the NCBI TaxonID as
the primary key of the taxon table, but as of BioSQL v1.0.1 that is
not true anymore. If you happen to rely on that former behavior in
your code, you will need to add a post-processing step to change the
primary keys to the NCBI taxon IDs.

=head1 ARGUMENTS

=over

=item --dbname

name of database to use

=item --sid

synonym for --dbname for Oracle folks

=item --dsn

the DSN of the database to connect to, overrides --dbname, --driver,
--host, and --port. The default is the value of the DBI_DSN
environment variable.

=item --driver

the DBD driver, one of mysql, Pg, or Oracle. If your driver is not
listed here, use --dsn instead.

=item --host

optional: host to connect with

=item --port

optional: port to connect with

=item --dbuser

optional: user name to connect with. The default is the value of the
DBI_USER environment variable.

=item --dbpass

optional: password to connect with. The default is the value of the
DBI_PASSWORD environment variable.

=item --schema

The schema under which the BioSQL tables reside in the database. For
Oracle and MySQL this is synonymous with the user, and will not have an
effect. PostgreSQL since v7.4 supports schemas as the namespace for
    collections of tables within a database.

=item --download

optional: whether to download new NCBI taxonomy data, default is no
download

=item --directory

optional: where to store/look for the data, default is ./taxdata

=item --nodelete

Flag meaning do not delete retired nodes.

You may want to specify this if you have sequence records referencing
the retired nodes if they happen to be leafs.  Otherwise you will get a
foreign key constraint failure saying something like 'child record
found' if there is a bioentry for that species. The retired nodes will
still be printed, so that you can then decide for yourself afterwards
    what to do with the bioentries that reference them.

=item --verbose=n

Sets the verbosity level, default is 1.

0 = silent,
1 = print current step,
2 = print current step and progress statistics.

=item --help

print this manual and exit

=item --allow_truncate

Flag to allow for non-transactional TRUNCATE.

This presently applies only to deleting and re-loading taxon names
table. The script will attempt to perform the much faster TRUNCATE
operation instead of a DELETE.  Some RDBMSs, like PostgreSQL, however
prohibit TRUNCATE from within a transactions, because they cannot roll
it back. If this flag is specified, the TRUNCATE will still be
performed, but then outside of a transaction. This means that between
the this operation is done until the names have been fully loaded
there will be no or only partial taxon names for querying, leading to
    inconsistent or incomplete answers to queries. This is therefore
disabled by default. Note though that for instance in PostgreSQL
    TRUNCATE is several orders of magnitude faster.

=item --chunksize

The number of rows after which to commit and possibly recompute
statistics.

This presently only applies to the nested set rebuild phase. It tries
to address the potentially marked performance degradation in
PostgreSQL while updating the taxon rows. The downside of this
approach is that because computing statistics in PostgreSQL cannot run
within a transaction, partially rebuilt nested set values have to be
committed at regular intervals. You can disable the chunked commits by
supplying a value of 0.

If you run on PostgreSQL and you are not sure about the performance
win, try --chunksize=0 --verbose=2. Watch the performance statistics
during the nested set rebuild phase. If you see a marked decrease in
rows/s over time down to values significantly below 100 rows/s, you
may want to run a chunked rebuild. Otherwise keep it disabled. For
database and query consistency disabling it is generally preferrable.

The default presently is to disable it. A suitable value for
PostgreSQL according to test runs would be 40,000.
"""