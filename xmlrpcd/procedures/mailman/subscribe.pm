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
    die "List $list is not allowed to subscribe\n";
  }

  subscribe($email, $list);

  return "ok";
}

#-----------------------------------------------------------------------------

sub subscribe {
  my ($email, $list) = @_;

  my $cin;
  open my $cout, ">>", "/dev/null";
  my @cmd = (
    "/usr/sbin/add_members",
      "--welcome-msg=n", "--admin-notify=n",
      "--regular-members-file=-",
      $list
  );
  my $pid = open3 $cin, $cout, $cout, @cmd;
  printf $cin "%s\n", $email;
  close $cin;
  waitpid $pid, 0;
}

#-----------------------------------------------------------------------------
1;
# vim:ft=perl
