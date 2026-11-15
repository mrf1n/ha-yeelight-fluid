"""Effect catalog helpers."""

from __future__ import annotations

from .const import DEFAULT_SPEED, DIRECTIONS, EffectMode, ProductInfo
from .device import YeelightFluidDevice
from .protocol import rgb_to_argb


class EffectCatalog:
    """Effects available on a product, filtered by firmware."""

    def __init__(self, product: ProductInfo, device: YeelightFluidDevice) -> None:
        self._product = product
        self._device = device
        self._reverse = {fw: app for app, fw in product.effect_mapping.items()}

    @property
    def modes(self) -> list[EffectMode]:
        fw = self._device.state.get("fw_version")
        try:
            fw_int = int(fw) if fw is not None else None
        except (TypeError, ValueError):
            fw_int = None
        return [m for m in self._product.effects if fw_int is None or fw_int >= m.min_firmware]

    @property
    def names(self) -> list[str]:
        return [m.name for m in self.modes]

    def by_name(self, name: str) -> EffectMode | None:
        return next((m for m in self._product.effects if m.name == name), None)

    def by_key(self, key: str) -> EffectMode | None:
        return next((m for m in self._product.effects if m.key == key), None)

    def by_firmware_id(self, firmware_id: int) -> EffectMode | None:
        app_id = self._reverse.get(firmware_id, firmware_id)
        return next((m for m in self._product.effects if m.value == app_id), None)

    def firmware_id(self, mode: EffectMode) -> int:
        return self._product.effect_mapping.get(mode.value, mode.value)

    def current(self) -> EffectMode | None:
        if self._device.effect_id:
            return self.by_firmware_id(self._device.effect_id)
        return None

    async def apply(
        self,
        mode: EffectMode,
        speed: int | None = None,
        colors: list[tuple[int, int, int]] | None = None,
        direction: str | None = None,
    ) -> None:
        cfg = self._device.effect_config
        if speed is None:
            speed = int(cfg.get("rate") or DEFAULT_SPEED)
        dir_value: int | None = None
        if mode.directions:
            if direction is None:
                dir_value = int(cfg.get("direction") or 0)
            else:
                dir_value = DIRECTIONS.index(direction)
        argb = None
        if colors and "color" in mode.capabilities:
            argb = [rgb_to_argb(c) for c in colors]
        await self._device.set_effect(
            self.firmware_id(mode), rate=speed, colors=argb, direction=dir_value
        )
