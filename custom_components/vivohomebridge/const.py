"""
Copyright 2024 vivo Mobile Communication Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");

   http://www.apache.org/licenses/LICENSE-2.0
"""

from homeassistant.const import Platform

DOMAIN = "vivohomebridge"
VIVO_HA_BRIDGE_VERSION = "1.0.0"
MANUFACTURER = "Home Assistant"
GLOB_NAME = "HA中控"
VHOME_URL = "https://iot.vivo.com.cn"
LOCAL_DISCOVERY_SERVICE_NAME = "vivohomebridge"
VIVO_HA_CONFIG_DATA_DEVICES_KEY = "config_devices"
VIVO_BRIDGE_DEVICE_NAME_CONFIG_KEY = "device_name"
VIVO_BRIDGE_DEVICE_ID_CLOUD_KEY = "deviceName"
VIVO_DEVICE_NAME_CONFIG_KEY = "dn"
VIVO_DEVICE_NAME_FRIENDLY_KEY = "friendly_name"
VIVO_BRIDGE_MAC_CONFIG_KEY = "mac"
VIVO_BRIDGE_HOST_CONFIG_KEY = "host"
VIVO_BRIDGE_PORT_CONFIG_KEY = "port"
VIVO_BRIDGE_USER_CODE_CONFIG_KEY = "user_code"
VIVO_BRIDGE_TMP_BIND_CODE_KEY = "tmp_bind_code"
VIVO_TIMEOUT_EXPIRED_TS = "timeout_expired_ts"
VIVO_DEVICE_ENTITY_ID_KEY = "entity_id"
# vivo BlueXlink Bridge下的设备ID
VIVO_DEVICE_ID_KEY = "device_id"
VIVO_BRIDGE_BOOT_UP_REASON_KEY = "boot_up_reason"

# #### vivo home bridge Component Event ####
EVENT_VHOME_DEV_ADD = "vhome_dev_add"
EVENT_VHOME_DEV_DEL = "vhome_dev_del"
EVENT_VHOME_DEV_REG_RESULT = "vhome_dev_reg_result"
EVENT_VHOME_DEV_UNREG_RESULT = "vhome_dev_unreg_result"
EVENT_VHOME_DEV_STATE_CHANGE = "vhome_dev_state_change"
EVENT_VHOME_DEV_STATE_FLUSH = "vhome_dev_state_flush"
EVENT_VHOME_DEV_SET_STATUS = "vhome_dev_set_status"
EVENT_VHOME_DEV_REMOVE_BRIDGE = "vhome_dev_remove_bridge"
EVEVT_VHOME_BRIDGE_ONLINE = "vhome_dev_online_bridge"
EVENT_VHOME_RECONNECT = "vhome_reconnect"

VIVO_HA_CONF_BIND_CODE = "bindCode"
VIVO_HA_CONF_DEVICE_TYPE = "deviceType"
VIVO_HA_CONF_DEVICE_LIST = "deviceList"
VIVO_HA_CONF_ADDABLE_DEVS = "addAbleDevices"
VIVO_HA_KEY_WORLD_DEV_LOGIC_MAC = "logicMac"
VIVO_HA_KEY_WORLD_DEV_ENTRY_ID = "config_entry_id"
VIVO_HA_KEY_WORLD_DEV_PHY_MAC = "phyMac"
VIVO_HA_KEY_WORLD_DEV_EN = "en"
VIVO_HA_PLATFORM_PKY_KEY = "pky"
VIVO_HA_PLATFORM_MANUFACTURER = "manufacturer_name"
VIVO_HA_KEY_WORLD_DEV_PROPS = "props"

# test env
if VHOME_URL == "https://iot.vivo.com.cn":
    NOTE_URL = "http://iot.vivo.com.cn/h5/223/"
    VIVO_HA_BRIDGE_PK = "ivfe7"
    VIVO_HA_PLATFORM_COVER_PK = "f2vxw"
    VIVO_HA_PLATFORM_FAN_PK = "wnihh"
    VIVO_HA_PLATFORM_LIGHT_PK = "y0d9r"
    VIVO_HA_PLATFORM_SOCKET_PK = "aq9j9"
    VIVO_HA_PLATFORM_OCCUPANCY_PK = "d2hn2"
    VIVO_HA_PLATFORM_HUMIDITY_TEMPERATURE_PK = "o0xsk"
    VIVO_HA_PLATFORM_OPENING_PK = "5xfgj"
    VIVO_HA_PLATFORM_SWITCH_PK = "o83kt"
    VIVO_HA_PLATFORM_CLIMATE_PK = "ur0xo"
    VIVO_HA_PLATFORM_MEDIA_PLAYER_PK = "dh5ek"
    VIVO_HA_PLATFORM_COMMON_SENSOR_PK = "b3e2a"
    VIVO_HA_PLATFORM_WATER_HEATER_PK = "0y2tk"
    VIVO_HA_PLATFORM_ILLUMINANCE_PK = "zcn0d"
    VIVO_HA_PLATFORM_CO2_PK          = "yltke"
    VIVO_HA_PLATFORM_CO_PK           = "x9dk8"
    VIVO_HA_PLATFORM_PH_PK           = "dh5w1"
    VIVO_HA_PLATFORM_PM1_PK          = "r4soc"
    VIVO_HA_PLATFORM_PM25_PK         = "wvpuh"
    VIVO_HA_PLATFORM_PM4_PK          = "jmquf"
    VIVO_HA_PLATFORM_PM10_PK         = "437yv"
    VIVO_HA_PLATFORM_POWER_PK        = "vjz6n"
    VIVO_HA_PLATFORM_CURRENT_PK      = "a07gv"
    VIVO_HA_PLATFORM_VOLTAGE_PK      = "l23nh"
    VIVO_HA_PLATFORM_ENERGY_PK       = "q7sfj"
    VIVO_HA_PLATFORM_BATTERY_PK      = "r4eno"
else:
    NOTE_URL = "http://iot-test.vivo.com.cn/h5/297/"
    VIVO_HA_BRIDGE_PK = "5vlwu"
    VIVO_HA_PLATFORM_LIGHT_PK = "kf0b8"
    VIVO_HA_PLATFORM_SOCKET_PK = "g371z"
    VIVO_HA_PLATFORM_SWITCH_PK = "0yklu"
    VIVO_HA_PLATFORM_CLIMATE_PK = "z31zp"
    VIVO_HA_PLATFORM_FAN_PK = "vhusg"
    VIVO_HA_PLATFORM_COVER_PK = "71ior"
    VIVO_HA_PLATFORM_OCCUPANCY_PK = "uj6o4"
    VIVO_HA_PLATFORM_OPENING_PK = "vp71c"
    VIVO_HA_PLATFORM_HUMIDITY_TEMPERATURE_PK = "28j5l"
    VIVO_HA_PLATFORM_MEDIA_PLAYER_PK = "t1a5r"
    VIVO_HA_PLATFORM_WATER_HEATER_PK = "3alex"
    VIVO_HA_PLATFORM_ILLUMINANCE_PK  = "5madq"
    VIVO_HA_PLATFORM_COMMON_SENSOR_PK = "bn5tx"
    VIVO_HA_PLATFORM_CO2_PK          = "yltke"
    VIVO_HA_PLATFORM_CO_PK           = "x9dk8"
    VIVO_HA_PLATFORM_PH_PK           = "dh5w1"
    VIVO_HA_PLATFORM_PM1_PK          = "r4soc"
    VIVO_HA_PLATFORM_PM25_PK         = "wvpuh"
    VIVO_HA_PLATFORM_PM4_PK          = "jmquf"
    VIVO_HA_PLATFORM_PM10_PK         = "437yv"
    VIVO_HA_PLATFORM_POWER_PK        = "vjz6n"
    VIVO_HA_PLATFORM_CURRENT_PK      = "a07gv"
    VIVO_HA_PLATFORM_VOLTAGE_PK      = "l23nh"
    VIVO_HA_PLATFORM_ENERGY_PK       = "q7sfj"
    VIVO_HA_PLATFORM_BATTERY_PK      = "r4eno"


VIVO_HA_PLATFORM_PK: dict = {
    Platform.LIGHT: VIVO_HA_PLATFORM_LIGHT_PK,
    Platform.SWITCH: VIVO_HA_PLATFORM_SOCKET_PK,
    Platform.CLIMATE: VIVO_HA_PLATFORM_CLIMATE_PK,
    Platform.FAN: VIVO_HA_PLATFORM_FAN_PK,
    Platform.COVER: VIVO_HA_PLATFORM_COVER_PK,
    Platform.MEDIA_PLAYER: VIVO_HA_PLATFORM_MEDIA_PLAYER_PK,
    Platform.REMOTE: VIVO_HA_PLATFORM_MEDIA_PLAYER_PK,
    Platform.SENSOR: VIVO_HA_PLATFORM_HUMIDITY_TEMPERATURE_PK,
    Platform.WATER_HEATER: VIVO_HA_PLATFORM_WATER_HEATER_PK,
    Platform.BINARY_SENSOR: VIVO_HA_PLATFORM_COMMON_SENSOR_PK,
}
