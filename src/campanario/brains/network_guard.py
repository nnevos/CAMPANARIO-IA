"""Defense-in-depth network guard for the *read-only* brain child process.

This intercepts ordinary Python socket calls while first-party adapters run.
It is intentionally NOT represented as an OS network sandbox: native libraries
or hostile code can bypass monkeypatches. Never use it for the Programacao brain.
"""
from __future__ import annotations

from contextlib import contextmanager
import socket


@contextmanager
def deny_worker_network():
    def denied(*args, **kwargs):
        raise PermissionError('worker_network_disabled')

    methods = ('connect', 'connect_ex', 'bind', 'listen', 'sendto')
    original = {name: getattr(socket.socket, name) for name in methods}
    create_connection = socket.create_connection
    getaddrinfo = socket.getaddrinfo
    try:
        for name in methods:
            setattr(socket.socket, name, denied)
        socket.create_connection = denied
        socket.getaddrinfo = denied
        yield
    finally:
        for name, method in original.items():
            setattr(socket.socket, name, method)
        socket.create_connection = create_connection
        socket.getaddrinfo = getaddrinfo
