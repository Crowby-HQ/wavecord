# SPDX-License-Identifier: MIT
"""Lavalink IP route planner status models."""

from __future__ import annotations

from abc import ABC
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List, Union

if TYPE_CHECKING:
    from .typings import (
        BaseDetails,
        FailingIPAddress,
        IPBlock as IPBlockPayload,
        NanoIPRouteDetails,
        RotatingIPRouteDetails,
        RotatingNanoIPRouteDetails,
    )

__all__ = (
    "IPRoutePlannerType",
    "IPBlockType",
    "IPBlock",
    "FailingAddress",
    "BaseIPRoutePlannerStatus",
    "RotatingIPRoutePlannerStatus",
    "NanoIPRoutePlannerStatus",
    "RotatingNanoIPRoutePlannerStatus",
    "BalancingIPRoutePlannerStatus",
    "RoutePlannerStatus",
)


# Enums
class IPRoutePlannerType(Enum):
    """The type of IP route planner configured on the Lavalink server.

    See the `Lavalink route planner docs`_ for more detail on when to use each.

    .. _Lavalink route planner docs:
        https://github.com/freyacodes/Lavalink/blob/master/ROUTEPLANNERS.md
    """

    ROTATING_IP = "RotatingIPRoutePlanner"
    """Switches the outbound IP on every ban (``RotateOnBan``)."""

    NANO_IP = "NanoIPRoutePlanner"
    """Switches the IP on every clock tick (``NanoSwitch``)."""

    ROTATING_NANO_IP = "RotatingNanoIPRoutePlanner"
    """Switches on clock tick and rotates the block on ban (``RotatingNanoSwitch``)."""

    BALANCING_IP = "BalancingIPRoutePlanner"
    """Selects an IP address randomly per request (``LoadBalance``)."""


class IPBlockType(Enum):
    """Whether the IP block is IPv4 or IPv6."""

    V4 = "Inet4Address"
    """An IPv4 address block."""

    V6 = "Inet6Address"
    """An IPv6 address block."""


# Data models
class IPBlock:
    """An IP address block reported by the route planner.

    Attributes
    ----------
    type : :class:`IPBlockType`
        Whether this is an IPv4 or IPv6 block.
    size : int
        The number of addresses in the block.
    """

    __slots__ = ("size", "type")

    def __init__(self, data: IPBlockPayload) -> None:
        self.type: IPBlockType = IPBlockType(data["type"])
        self.size: int = int(data["size"])

    def __repr__(self) -> str:
        return f"<IPBlock type={self.type.name} size={self.size}>"


class FailingAddress:
    """An IP address that is currently failing (banned by the platform).

    Attributes
    ----------
    address : str
        The IP address string.
    failed_at : :class:`datetime.datetime`
        When the address was marked as failing (UTC).
    """

    __slots__ = ("address", "failed_at")

    def __init__(self, data: FailingIPAddress) -> None:
        self.address: str = data["address"]
        self.failed_at: datetime = datetime.fromtimestamp(
            data["failingTimestamp"] / 1000, tz=timezone.utc
        )

    def __repr__(self) -> str:
        return f"<FailingAddress address={self.address!r} failed_at={self.failed_at}>"


# Status base
class BaseIPRoutePlannerStatus(ABC):
    r"""Abstract base class for all IP route planner status objects.

    Attributes
    ----------
    ip_block : :class:`IPBlock`
        The configured IP block.
    failing_addresses : list[:class:`FailingAddress`]
        Addresses that are currently banned / failing.
    type : :class:`IPRoutePlannerType`
        The concrete planner type (set on each subclass).
    """

    __slots__ = ("failing_addresses", "ip_block")

    type: IPRoutePlannerType

    def __init__(self, data: BaseDetails) -> None:
        self.ip_block: IPBlock = IPBlock(data["ipBlock"])
        self.failing_addresses: List[FailingAddress] = [
            FailingAddress(addr) for addr in data["failingAddresses"]
        ]


# Concrete status classes
class RotatingIPRoutePlannerStatus(BaseIPRoutePlannerStatus):
    """Status for the ``RotatingIPRoutePlanner``.

    Attributes
    ----------
    type : :attr:`IPRoutePlannerType.ROTATING_IP`
    current_address : str
        The IP address currently in use.
    rotate_index : int
        How many times the planner has rotated.
    ip_index : int
        The index within the block of the current address.
    """

    __slots__ = ("current_address", "ip_index", "rotate_index")

    type = IPRoutePlannerType.ROTATING_IP

    def __init__(self, data: RotatingIPRouteDetails) -> None:
        super().__init__(data)
        self.rotate_index: int = int(data["rotateIndex"])
        self.ip_index: int = int(data["ipIndex"])
        self.current_address: str = data["currentAddress"]

    def __repr__(self) -> str:
        return (
            f"<RotatingIPRoutePlannerStatus "
            f"current={self.current_address!r} "
            f"rotations={self.rotate_index}>"
        )


class NanoIPRoutePlannerStatus(BaseIPRoutePlannerStatus):
    """Status for the ``NanoIPRoutePlanner``.

    Attributes
    ----------
    type : :attr:`IPRoutePlannerType.NANO_IP`
    current_address_index : int
        The index of the current IP address in the block.
    """

    __slots__ = ("current_address_index",)

    type = IPRoutePlannerType.NANO_IP

    def __init__(self, data: NanoIPRouteDetails) -> None:
        super().__init__(data)
        self.current_address_index: int = int(data["currentAddressIndex"])

    def __repr__(self) -> str:
        return (
            f"<NanoIPRoutePlannerStatus "
            f"current_index={self.current_address_index}>"
        )


class RotatingNanoIPRoutePlannerStatus(BaseIPRoutePlannerStatus):
    """Status for the ``RotatingNanoIPRoutePlanner``.

    Attributes
    ----------
    type : :attr:`IPRoutePlannerType.ROTATING_NANO_IP`
    block_index : int
        The index of the current block.
    current_address_index : int
        The index of the current address within the block.
    """

    __slots__ = ("block_index", "current_address_index")

    type = IPRoutePlannerType.ROTATING_NANO_IP

    def __init__(self, data: RotatingNanoIPRouteDetails) -> None:
        super().__init__(data)
        self.block_index: int = int(data["blockIndex"])
        self.current_address_index: int = int(data["currentAddressIndex"])

    def __repr__(self) -> str:
        return (
            f"<RotatingNanoIPRoutePlannerStatus "
            f"block={self.block_index} "
            f"address_index={self.current_address_index}>"
        )


class BalancingIPRoutePlannerStatus(BaseIPRoutePlannerStatus):
    """Status for the ``BalancingIPRoutePlanner``.

    Attributes
    ----------
    type : :attr:`IPRoutePlannerType.BALANCING_IP`
    """

    type = IPRoutePlannerType.BALANCING_IP

    def __repr__(self) -> str:
        return (
            f"<BalancingIPRoutePlannerStatus "
            f"failing={len(self.failing_addresses)}>"
        )


RoutePlannerStatus = Union[
    RotatingIPRoutePlannerStatus,
    NanoIPRoutePlannerStatus,
    RotatingNanoIPRoutePlannerStatus,
    BalancingIPRoutePlannerStatus,
]
"""Union type alias for all concrete route planner status classes.

Check :attr:`BaseIPRoutePlannerStatus.type` to distinguish them.
"""
