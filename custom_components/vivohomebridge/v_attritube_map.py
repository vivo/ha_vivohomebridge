"""
Copyright 2024 vivo Mobile Communication Co., Ltd.
Licensed under the Apache License, Version 2.0 (the "License");

   http://www.apache.org/licenses/LICENSE-2.0
"""

from homeassistant.components.climate import ATTR_HVAC_MODES, ATTR_FAN_MODES
from homeassistant.components.fan import ATTR_PRESET_MODES
from homeassistant.const import Platform
from .v_attribute import *

v2h_attributes_map = {
    "commom": [
        {
            VIVO_KEY_WORD_NAME: VIVO_HA_COMMOM_ATTR_SOFTVER,
            "value_type": "string",
            "format": "string",
            "unit": "",
            "description": "固件版本",
            "access": ["read", "notify"],
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_HA_COMMOM_ATTR_HARDVER,
            "value_type": "string",
            "format": "string",
            "unit": "",
            "description": "硬件版本",
            "access": ["read", "notify"],
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_HA_COMMOM_ATTR_VENDOR,
            "value_type": "string",
            "format": "string",
            "unit": "",
            "description": "制造商",
            "access": ["read", "notify"],
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_HA_COMMON_ATTR_SERIAL,
            "value_type": "string",
            "format": "string",
            "unit": "",
            "description": "序列号",
            "access": ["read", "notify"],
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_HA_COMMON_ATTR_MODEL,
            "value_type": "string",
            "format": "string",
            "unit": "",
            "description": "型号",
            "access": ["read", "notify"],
        },
    ],
    Platform.LIGHT: [
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_POWER,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_POWER,
            "description": "电源",
            "value_type": "string",
            "format": "string",
            "unit": "",
            "value_list": [
                {
                    "value": "on",
                    "description": "开"
                },
                {
                    "value": "off",
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_brightness",
            VIVO_KEY_WORD_H_NAME: "brightness",
            "description": "亮度",
            "value_type": "number",
            "format": "int",
            "value_range": [
                10,
                100,
                1
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": "%",
            "step": 1,
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_color_rgb",
            VIVO_KEY_WORD_H_NAME: "rgb_color",
            "description": "颜色",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "*",
                    "description": "RGB设置"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": ""
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_light_temperature",
            VIVO_KEY_WORD_H_NAME: "color_temp_kelvin",
            "description": "色温",
            "value_type": "number",
            "format": "int",
            "value_range": [
                1000,
                8000,
                1
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": "K",
            "step": 1,
        },
    ],
    Platform.SWITCH: [
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_POWER,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_POWER,
            "description": "开关",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "on",
                    "description": "开"
                },
                {
                    "value": "off",
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        }
    ],
    Platform.CLIMATE: [
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_POWER,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_POWER,
            "description": "电源",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "on",
                    "description": "开"
                },
                {
                    "value": "off",
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_mode",
            VIVO_KEY_WORD_H_NAME: ATTR_HVAC_MODES,
            "description": "模式",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "auto",
                    "h_value": "auto",
                    "description": "自动模式"
                },
                {
                    "value": "heat",
                    "h_value": "heat",
                    "description": "制热模式"
                },
                {
                    "value": "cool",
                    "h_value": "cool",
                    "description": "制冷模式"
                },
                {
                    "value": "dry",
                    "h_value": "dry",
                    "description": "除湿模式"
                },
                {
                    "value": "fan",
                    "h_value": "fan_only",
                    "description": "送风模式"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": ""
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_temperature",
            VIVO_KEY_WORD_H_NAME: "target_temperature",
            "description": "目标温度",
            "value_type": "number",
            "format": "float",
            "value_range": [
                16,
                32,
                1
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": "℃"
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_wind_speed",
            VIVO_KEY_WORD_H_NAME: ATTR_FAN_MODES,
            "description": "风速",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "high",
                    "h_value": "high",
                    "description": "高风"
                },
                {
                    "value": "middle",
                    "h_value": "medium",
                    "description": "中风"
                },
                {
                    "value": "low",
                    "h_value": "low",
                    "description": "低风"
                },
                {
                    "value": "auto",
                    "h_value": "auto",
                    "description": "自动风"
                },
                {
                    "value": "middle_high",
                    "h_value": "middle_high",
                    "description": "中高风"
                },
                {
                    "value": "middle_low",
                    "h_value": "middle_low",
                    "description": "中低风"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": ""
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_wind_swing_up_down",
            VIVO_KEY_WORD_H_NAME: VIVO_CLIMATE_SWING_MODE_VERTICAL_H_NAME,
            "description": "上下扫风",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "on",
                    "h_value": "vertical",
                    "description": "开"
                },
                {
                    "value": "off",
                    "h_value": "off",
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_wind_swing_left_right",
            VIVO_KEY_WORD_H_NAME: VIVO_CLIMATE_SWING_MODE_HORIZONTAL_H_NAME,
            "description": "左右扫风",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "on",
                    "h_value": "horizontal",
                    "description": "开"
                },
                {
                    "value": "off",
                    "h_value": "off",
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_indoor_temperature",
            VIVO_KEY_WORD_H_NAME: "current_temperature",
            "description": "室内温度",
            "value_type": "number",
            "format": "float",
            "value_range": [
                1,
                100,
                1
            ],
            "access": [
                "read",
                "notify"
            ],
            "unit": "℃"
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_indoor_humidity",
            VIVO_KEY_WORD_H_NAME: "current_humidity",
            "description": "室内湿度",
            "value_type": "number",
            "format": "int",
            "value_range": [
                1,
                100,
                1
            ],
            "access": [
                "read",
                "notify"
            ],
            "unit": "%"
        }
    ],
    Platform.FAN: [
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_POWER,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_POWER,
            "description": "电源",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "on",
                    "description": "开"
                },
                {
                    "value": "off",
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        }, {
            VIVO_KEY_WORD_NAME: "vivo_std_swing",
            VIVO_KEY_WORD_H_NAME: "oscillating",
            "description": "摇头",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "on",
                    "description": "开"
                },
                {
                    "value": "off",
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        }, {
            VIVO_KEY_WORD_NAME: "vivo_std_mode",
            VIVO_KEY_WORD_H_NAME: ATTR_PRESET_MODES,
            "description": "工作模式",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "auto",
                    "h_value": "Smart",
                    "description": "自动风"
                },
                {
                    "value": "normal",
                    "h_value": "Straight Wind",
                    "description": "正常风"
                },
                {
                    "value": "natural",
                    "h_value": "Natural Wind",
                    "description": "自然风"
                },
                {
                    "value": "sleep",
                    "h_value": "Sleep",
                    "description": "睡眠风"
                },
                {
                    "value": "comfort",
                    "h_value": "comfort",
                    "description": "舒适风"
                },
                {
                    "value": "warm",
                    "h_value": "warm",
                    "description": "暖风"
                },
                {
                    "value": "feel",
                    "h_value": "feel",
                    "description": "人感"
                },
                {
                    "value": "baby",
                    "h_value": "baby",
                    "description": "宝宝风"
                },
                {
                    "value": "mute",
                    "h_value": "mute",
                    "description": "静音风"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": ""
        }, {
            VIVO_KEY_WORD_NAME: "vivo_std_speed_gear",
            VIVO_KEY_WORD_H_NAME: "percentage",
            "description": "风速档位",
            "value_type": "number",
            "format": "int",
            "value_range": [
                FAN_MIN_SPEED,
                FAN_MAX_SPEED,
                FAN_SPEED_STEP
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": "%"
        }
    ],
    Platform.COVER: [
        {
            VIVO_KEY_WORD_NAME: "vivo_std_window_covering",
            VIVO_KEY_WORD_H_NAME: "current_position",
            "description": "窗帘闭合",
            "value_type": "number",
            "format": "int",
            "value_range": [
                0,
                100,
                1
            ],
            "access": [
                "read",
                "notify"
            ],
            "unit": "%"
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_window_open",
            VIVO_KEY_WORD_H_NAME: "open",
            "description": "窗帘全开",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "open",
                    "h_value": "open",
                    "description": "开"
                }
            ]
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_window_close",
            VIVO_KEY_WORD_H_NAME: "close",
            "description": "窗帘全关",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "close",
                    "h_value": "close",
                    "description": "关"
                }
            ]
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_window_pause",
            VIVO_KEY_WORD_H_NAME: "stop",
            "description": "窗帘暂停",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": "pause",
                    "h_value": "stop",
                    "description": "暂停"
                }
            ]
        }
    ],
    Platform.MEDIA_PLAYER: [
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_POWER,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_POWER,
            "description": "开关",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_POWER_ON,
                    "description": "开"
                },
                {
                    "value": VIVO_ATTR_VALUE_POWER_OFF,
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_PAUSE,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PAUSE,
            "description": "暂停",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_PAUSE,
                    "description": "暂停"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_PLAY,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PLAY,
            "description": "播放",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_PLAY,
                    "description": "播放"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_STOP,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_STOP,
            "description": "停止",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_STOP,
                    "description": "停止"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_MUTE,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_MUTE,
            "description": "静音",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_MUTE,
                    "description": "静音"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_VOLUME,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME,
            "description": "调节音量",
            "value_type": "number",
            "format": "int",
            "value_range": [
                1,
                100,
                1
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": "%"
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_VOLUME_UP,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME_UP,
            "description": "音量+",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_VOLUME_UP,
                    "description": "音量+"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_VOLUME_DOWN,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME_DOWN,
            "description": "音量-",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_VOLUME_DOWN,
                    "description": "音量-"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_VOLUME_UP,
            VIVO_KEY_WORD_H_NAME: HA_LG_ATTR_NAME_VOLUME_UP,
            "description": "音量+",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_VOLUME_UP,
                    "description": "音量+"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_VOLUME_DOWN,
            VIVO_KEY_WORD_H_NAME: HA_LG_ATTR_NAME_VOLUME_DOWN,
            "description": "音量-",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_VOLUME_DOWN,
                    "description": "音量-"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_NEXT,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_NEXT,
            "description": "后",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_NEXT,
                    "description": "后"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_PREVIOUS,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PREVIOUS,
            "description": "前",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_PREVIOUS,
                    "description": "前"
                }
            ],
            "access": [
                "write"
            ]
        },
        # media play left
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_LEFT,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_LEFT,
            "description": "左",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_LEFT,
                    "description": "左"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_RIGHT,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_RIGHT,
            "description": "右",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_RIGHT,
                    "description": "右"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_UP,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_UP,
            "description": "上",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_UP,
                    "description": "上"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_DOWN,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_DOWN,
            "description": "下",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_DOWN,
                    "description": "下"
                }
            ],
            "access": [
                "write"
            ]
        }, {  # media play home
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_HOME,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_HOME,
            "description": "主页",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_HOME,
                    "description": "主页"
                }
            ],
            "access": [
                "write"
            ]
        }, {  # media play menu
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_MENU,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_MENU,
            "description": "菜单",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_MENU,
                    "description": "菜单"
                }
            ],
            "access": [
                "write"
            ]
        }, {  # media play back
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_BACK,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_BACK,
            "description": "返回",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_BACK,
                    "description": "返回"
                }
            ],
            "access": [
                "write"
            ]
        }, {  # media play enter
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_ENTER,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_ENTER,
            "description": "确认",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_ENTER,
                    "description": "确认"
                }
            ],
            "access": [
                "write"
            ]
        }

    ],
    Platform.REMOTE: [
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_POWER,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_POWER,
            "description": "开关",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_POWER_ON,
                    "description": "开"
                },
                {
                    "value": VIVO_ATTR_VALUE_POWER_OFF,
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_REMOTE_POWER,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_REMOTE_POWER,
            "description": "遥控开关",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_REMOTE_POWER_ON,
                    "description": "开"
                },
                {
                    "value": VIVO_ATTR_VALUE_REMOTE_POWER_OFF,
                    "description": "关"
                }
            ],
            "access": [
                "write",
                "read",
                "notify"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_PAUSE,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PAUSE,
            "description": "暂停",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_PAUSE,
                    "description": "暂停"
                }
            ],
            "access": [
                "write"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_PLAY,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PLAY,
            "description": "播放",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_PLAY,
                    "description": "播放"
                }
            ],
            "access": [
                "write"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_STOP,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_STOP,
            "description": "停止",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_STOP,
                    "description": "停止"
                }
            ],
            "access": [
                "write"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_MUTE,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_MUTE,
            "description": "静音",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_MUTE,
                    "description": "静音"
                }
            ],
            "access": [
                "write"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_VOLUME,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME,
            "description": "调节音量",
            "value_type": "number",
            "format": "int",
            "value_range": [
                1,
                100,
                1
            ],
            "access": [
                "write",
                "read",
                "notify"
            ],
            "unit": "%"
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_VOLUME_UP,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME_UP,
            "description": "音量+",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_VOLUME_UP,
                    "description": "音量+"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_VOLUME_DOWN,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_VOLUME_DOWN,
            "description": "音量-",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_VOLUME_DOWN,
                    "description": "音量-"
                }
            ],
            "access": [
                "write"
            ],
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_MENU,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_MENU,
            "description": "功能菜单",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_MENU,
                    "description": "功能菜单"
                }
            ],
            "access": [
                "write"
            ],
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_BACK,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_BACK,
            "description": "返回",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_BACK,
                    "description": "返回"
                }
            ],
            "access": [
                "write"
            ],
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_ENTER,
            VIVO_KEY_WORD_H_NAME: HA_APPLE_ATTR_NAME_ENTER,
            "description": "确认",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_ENTER,
                    "description": "确认"
                }
            ],
            "access": [
                "write"
            ],
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_UP,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_UP,
            "description": "上",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_UP,
                    "description": "上"
                }
            ],
            "access": [
                "write"
            ],
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_DOWN,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_DOWN,
            "description": "下",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_DOWN,
                    "description": "下"
                }
            ],
            "access": [
                "write"
            ],
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_LEFT,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_LEFT,
            "description": "左",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_LEFT,
                    "description": "左"
                }
            ],
            "access": [
                "write"
            ],
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_RIGHT,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_RIGHT,
            "description": "右",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_RIGHT,
                    "description": "右"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_NEXT,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_NEXT,
            "description": "后",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_NEXT,
                    "description": "后"
                }
            ],
            "access": [
                "write"
            ],
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_PREVIOUS,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_PREVIOUS,
            "description": "前",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_PREVIOUS,
                    "description": "前"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_HOME,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_HOME,
            "description": "主页",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_HOME,
                    "description": "主页"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_WAKE_UP,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_WAKE_UP,
            "description": "唤醒",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_WAKE_UP,
                    "description": "唤醒"
                }
            ],
            "access": [
                "write"
            ]
        }, {
            VIVO_KEY_WORD_NAME: VIVO_ATTR_NAME_TOP_MENU,
            VIVO_KEY_WORD_H_NAME: HA_ATTR_NAME_WAKE_UP,
            "description": "顶部菜单",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {
                    "value": VIVO_ATTR_VALUE_TOP_MENU,
                    "description": "顶部菜单"
                }
            ],
            "access": [
                "write"
            ]
        }
    ],
    Platform.SENSOR: [
        {
            VIVO_KEY_WORD_NAME: "vivo_std_onoff",
            VIVO_KEY_WORD_H_NAME: "power",
            "description": "开关",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {"value": "on", "description": "开"},
                {"value": "off", "description": "关"},
            ],
            "access": ["read", "notify"],
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_person_move",
            VIVO_KEY_WORD_H_NAME: "move",
            "description": "人体移动",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {"value": "true", "description": "检测到移动"},
                {"value": "false", "description": "未检测到移动"},
            ],
            "access": ["read", "notify"],
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_humidity",
            VIVO_KEY_WORD_H_NAME: "current_humidity",
            "description": "湿度",
            "value_type": "number",
            "format": "int",
            "value_range": [0, 100, 1],
            "access": ["read", "notify"],
            "unit": "%",
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_temperature",
            VIVO_KEY_WORD_H_NAME: "current_temperature",
            "description": "温度",
            "value_type": "number",
            "format": "int",
            "value_range": [-100, 100, 1],
            "access": ["read", "notify"],
            "unit": "℃",
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_illuminance",
            VIVO_KEY_WORD_H_NAME: "illuminance",
            "description": "光照",
            "value_type": "number",
            "format": "int",
            "value_range": [-100, 100, 1],
            "access": ["read", "notify"],
            "unit": "lx",
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_sensor_value",
            VIVO_KEY_WORD_H_NAME: "sensor_value",
            "description": "传感器值",
            "value_type": "string",
            "format": "string",
            "value_list": [
                {"value": "*", "description": "*", "compare": "*"},
            ],
            "unit": "",
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_battery",
            VIVO_KEY_WORD_H_NAME: "battery",
            "description": "电池电量",
            "value_type": "number",
            "format": "int",
            "value_range": [0, 100, 1],
            "access": ["read", "notify"],
            "unit": "%",
        },
        {
            VIVO_KEY_WORD_H_NAME:"power",
            "mW": {
                VIVO_KEY_WORD_NAME: "vivo_std_mW",
                "description": "功率(毫瓦)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    100000,
                    0.001
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "mW"
            },
            "W": {
                VIVO_KEY_WORD_NAME: "vivo_std_W",
                "description": "功率(瓦特)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    1000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "W"
            },
            "kW": {
                VIVO_KEY_WORD_NAME: "vivo_std_kW",
                "description": "功率(千瓦)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    1000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "kW"
            },
            "MW": {
                VIVO_KEY_WORD_NAME: "vivo_std_M_W",
                "description": "功率(兆瓦)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    1000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "MW"
            },
            "GW": {
                VIVO_KEY_WORD_NAME: "vivo_std_GW",
                "description": "功率(吉瓦)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    1000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "GW"
            },
            "TW": {
                VIVO_KEY_WORD_NAME: "vivo_std_TW",
                "description": "功率(太瓦)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    1000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "TW"
            }
        },
        {
            VIVO_KEY_WORD_H_NAME:"voltage",
            "µV": {
                VIVO_KEY_WORD_NAME: "vivo_std_µV",
                "description": "电压(微伏)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    1000,
                    0.001
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "µV"
            },
            "mV": {
                VIVO_KEY_WORD_NAME: "vivo_std_mV",
                "description": "电压(毫伏)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    1000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "mV"
            },
            "V": {
                VIVO_KEY_WORD_NAME: "vivo_std_V",
                "description": "电压(伏特)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    1000,
                    0.1
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "V"
            },
            "kV": {
                VIVO_KEY_WORD_NAME: "vivo_std_kV",
                "description": "电压(千伏)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    1000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "kV"
            }
        },
        {
            VIVO_KEY_WORD_H_NAME:"energy",
            "mWh": {
                VIVO_KEY_WORD_NAME: "vivo_std_mWh",
                "description": "耗电量(毫瓦时)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    100000,
                    0.001
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "mWh"
            },
            "Wh": {
                VIVO_KEY_WORD_NAME: "vivo_std_Wh",
                "description": "耗电量(瓦时)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    100000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "Wh"
            },
            "kWh": {
                VIVO_KEY_WORD_NAME: "vivo_std_kWh",
                "description": "耗电量(千瓦时/度)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    100000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "kWh"
            },
            "MWh": {
                VIVO_KEY_WORD_NAME: "vivo_std_M_Wh",
                "description": "耗电量(兆瓦时)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    100000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "MWh"
            },
            "GWh": {
                VIVO_KEY_WORD_NAME: "vivo_std_GWh",
                "description": "耗电量(吉瓦时)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    100000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "GWh"
            },
            "TWh": {
                VIVO_KEY_WORD_NAME: "vivo_std_TWh",
                "description": "耗电量(太瓦时)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    100000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "TWh"
            }
        },
        {
            VIVO_KEY_WORD_H_NAME: "current",
            "mA": {
                VIVO_KEY_WORD_NAME: "vivo_std_mA",
                "description": "电流(毫安)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    100000,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "mA"
            },
            "A": {
                VIVO_KEY_WORD_NAME: "vivo_std_A",
                "description": "电流(安培)",
                "value_type": "number",
                "format": "float",
                "value_range": [
                    0,
                    100,
                    0.01
                ],
                "access": [
                    "read",
                    "notify"
                ],
                "unit": "A"
            }
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_ph",
            VIVO_KEY_WORD_H_NAME: "ph",
            "description": "PH值",
            "value_type": "number",
            "format": "float",
            "value_range": [
                0,
                14,
                0.01
            ],
            "access": [
                "read",
                "notify"
            ]
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_pm1",
            VIVO_KEY_WORD_H_NAME: "pm1",
            "description": "PM1值",
            "value_type": "number",
            "format": "float",
            "value_range": [
                0,
                300,
                0.01
            ],
            "access": [
                "read",
                "notify"
            ],
            "unit": "µg/m³"
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_pm25",
            VIVO_KEY_WORD_H_NAME: "pm25",
            "description": "PM2.5值",
            "value_type": "number",
            "format": "float",
            "value_range": [
                0,
                300,
                0.01
            ],
            "access": [
                "read",
                "notify"
            ],
            "unit": "µg/m³"
        },
        {
            VIVO_KEY_WORD_NAME: "vivo_std_pm10",
            VIVO_KEY_WORD_H_NAME: "pm10",
            "description": "PM10值",
            "value_type": "number",
            "format": "float",
            "value_range": [
                0,
                300,
                0.01
            ],
            "access": [
                "read",
                "notify"
            ],
            "unit": "µg/m³"
        },
    ]

}


@staticmethod
def get_h_attribute_name(platform, name: str):
    attributes = v2h_attributes_map.get(platform, [])
    for attribute in attributes:
        if attribute[VIVO_KEY_WORD_NAME] == name:
            return attribute[VIVO_KEY_WORD_H_NAME]
    return None


@staticmethod
def get_v_attribute_name(platform, h_name: str):
    attributes = v2h_attributes_map.get(platform, [])
    for attribute in attributes:
        if attribute[VIVO_KEY_WORD_H_NAME] == h_name:
            return attribute[VIVO_KEY_WORD_NAME]
    return None
