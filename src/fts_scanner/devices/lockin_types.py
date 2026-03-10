from __future__ import annotations


class LockInAdapterType:
    """Supported lock-in transport adapters."""

    KEYSIGHT_VISA = "keysight_visa"
    PROLOGIX_ETHERNET = "prologix_ethernet"
    PROLOGIX_USB = "prologix_usb"


LOCKIN_ADAPTER_LABELS: dict[str, str] = {
    LockInAdapterType.KEYSIGHT_VISA: "Keysight VISA",
    LockInAdapterType.PROLOGIX_ETHERNET: "Prologix Ethernet",
    LockInAdapterType.PROLOGIX_USB: "Prologix USB",
}
