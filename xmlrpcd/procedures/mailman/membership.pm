#!/usr/bin/perl

#-----------------------------------------------------------------------------

use YAML;
use Frontier::RPC2;

my $CONFIG_DIR = "/var/lib/xmlrpcd/etc";
my $CONFIG_FILE = "$CONFIG_DIR/lists.yaml";

my $FALSE = Frontier::RPC2->new->boolean(0);
my $TRUE  = Frontier::RPC2->new->boolean(1);

#-----------------------------------------------------------------------------

our $RPC_UID = "root";
our $RPC_GID = "root";

#-----------------------------------------------------------------------------

sub entry_point {
  my ($email) = @_;

  my $config = YAML::LoadFile($CONFIG_FILE);

  my $matches = {
    public => {},
    internal => {},
  };
  for my $list (keys %{ $config->{public} }) {
    $matches->{public}{$list} = {
      description => $config->{public}{$list}{description},
      address     => $config->{public}{$list}{address},
      subscribed  => is_member($email, $list) ? $TRUE : $FALSE,
    };
  }
  for my $list (keys %{ $config->{members} }) {
    $matches->{internal}{$list} = {
      description => $config->{members}{$list}{description},
      address     => $config->{members}{$list}{address},
      subscribed  => is_member($email, $list) ? $TRUE : $FALSE,
    };
  }

  return $matches;
}

#-----------------------------------------------------------------------------

sub is_member {
  my ($email, $list) = @_;

  return scalar grep { $_ eq $email } list_members($list);
}

sub list_members {
  my ($list) = @_;

  open my $f, "-|", "/usr/sbin/list_members", "--regular", $list;
  my @emails = <$f>;
  chomp @emails;
  close $f;

  return @emails;
}

#-----------------------------------------------------------------------------
1;
# vim:ft=perl
