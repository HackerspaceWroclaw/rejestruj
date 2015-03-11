#!/usr/bin/perl

#-----------------------------------------------------------------------------

use IPC::Open3;
use YAML;

my $CONFIG_DIR = "/var/lib/xmlrpcd/etc";
my $CONFIG_FILE = "$CONFIG_DIR/lists.yaml";

#-----------------------------------------------------------------------------

our $RPC_UID = "root";
our $RPC_GID = "root";

#-----------------------------------------------------------------------------

sub entry_point {
  my ($email, $list) = @_;

  my $config = YAML::LoadFile($CONFIG_FILE);
  if (!exists $config->{public}{$list} && !exists $config->{members}{$list}) {
    die "List $list is not allowed to unsubscribe\n";
  }

  unsubscribe($email, $list);

  return "ok";
}

#-----------------------------------------------------------------------------

sub unsubscribe {
  my ($email, $list) = @_;

  open my $cin, "<", "/dev/null";
  open my $cout, ">>", "/dev/null";
  my @cmd = (
    "/usr/sbin/remove_members",
      "--nouserack", "--noadminack",
      $list, $email
  );
  my $pid = open3 $cin, $cout, $cout, @cmd;
  waitpid $pid, 0;
}

#-----------------------------------------------------------------------------
1;
# vim:ft=perl
