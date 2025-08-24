"""Unsupported models registry."""

from __future__ import annotations
import os
import importlib.util
from .enum import Model
from .logger import _LOGGER
from homeassistant.core import HomeAssistant


async def get_combined_unsupported(hass: HomeAssistant) -> dict[str, list[Model]]:
    
    """Merge the UNSUPPORTED principal with the user's if it exists."""
    
    combined = {k: v.copy() for k, v in UNSUPPORTED.items()} 

    user_file = os.path.join(os.path.dirname(__file__), "unsupported_user.py")
    if not os.path.exists(user_file):
        return combined  

    try:
        spec = importlib.util.spec_from_file_location("unsupported_user", user_file)
        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        user_data = getattr(user_module, "UNSUPPORTED", {})
        if isinstance(user_data, dict):
            for key, value in user_data.items():
                if key not in combined:
                    combined[key] = []
                for model in value:
                    if model not in combined[key]:
                        combined[key].append(model)
    except Exception as e:
        await hass.async_add_executor_job(_LOGGER.debug,"[MiWiFi] Error loading unsupported_user.py: %s",e)

    return combined


async def is_feature_unsupported(hass: HomeAssistant, feature: str, model: str) -> bool:
    """Check if a feature is unsupported for a given model."""
    unsupported = await get_combined_unsupported(hass)
    return model in unsupported.get(feature, [])


async def safe_call_with_support(hass, luci, feature: str, coro, model: str):
    """Safely call a Luci API, skipping unsupported features and returning placeholders."""
    if await is_feature_unsupported(hass, feature, model):
        _LOGGER.info("⚠️ [MiWiFi] Skipping unsupported feature '%s' for model '%s'", feature, model)
        return {"error": "unsupported"}
    try:
        result = await coro
        if not result:
            _LOGGER.warning("❌ [MiWiFi] No data returned for '%s' on model '%s'", feature, model)
            return {"error": "no data"}
        return result
    except Exception as e:
        _LOGGER.warning("❌ [MiWiFi] Failed to get '%s' on model '%s': %s", feature, model, e)
        return {"error": "no data"}



UNSUPPORTED: dict[str, list[Model]] = {
    "new_status": [
        Model.R1D,
        Model.R2D,
        Model.R1CM,
        Model.R1CL,
        Model.R3P,
        Model.R3D,
        Model.R3L,
        Model.R3A,
        Model.R3,
        Model.R3G,
        Model.R4,
        Model.R4A,
        Model.R4AC,
        Model.R4C,
        Model.R4CM,
        Model.D01,
        Model.RN06,
    ],
    
    "wifi_config": [
        Model.CR8806,
    ],

    "mac_filter": [
        Model.RM1800
        ],
    
    "mac_filter_info":[
    ],

    "qos_info": [],
    "vpn_control": [],
}
