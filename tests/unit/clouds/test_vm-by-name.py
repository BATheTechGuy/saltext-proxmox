"""
Unit test for the _get_vm_by_name KeyError fix.

Regression test for: cluster/resources (filtered to type=vm) can return
VM/CT entries with no 'name' key -- e.g. guests created without an
explicit name/hostname, or caught mid-creation. Direct dict access
(vm["name"]) raised KeyError on the first such entry encountered before
a real match was found.
"""
from unittest.mock import patch

import pytest

from salt.exceptions import SaltCloudNotFound
from saltext.proxmox.clouds import proxmox


@pytest.fixture
def configure_loader_modules():
    return {proxmox: {"__opts__": {}}}


def test_get_vm_by_name_skips_entries_without_name_key():
    """
    _get_vm_by_name should skip VM/CT entries that have no 'name' key
    instead of raising KeyError, and still find and return the correct
    entry further down the list.
    """
    resources = [
        {"type": "qemu", "vmid": 100},  # unnamed VM, no 'name' key at all
        {"type": "lxc", "name": "k3s-worker-01", "vmid": 21101},
    ]

    with patch.object(proxmox, "_query", return_value=resources):
        result = proxmox._get_vm_by_name("k3s-worker-01")

    assert result == {"type": "lxc", "name": "k3s-worker-01", "vmid": 21101}


def test_get_vm_by_name_raises_not_found_when_no_match():
    """
    A name matching nothing in the list (including entries with no
    'name' key present) should raise SaltCloudNotFound, not KeyError.
    """
    resources = [
        {"type": "qemu", "vmid": 100},
        {"type": "lxc", "name": "some-other-container", "vmid": 999},
    ]

    with patch.object(proxmox, "_query", return_value=resources):
        with pytest.raises(SaltCloudNotFound):
            proxmox._get_vm_by_name("k3s-worker-01")
