"""
玩家动作解析器

将玩家的自然语言指令转换为游戏内的动作。
支持 OpenAI / MiniMax 等兼容 GPT-4o 的模型。
"""
from __future__ import annotations
import json
import re
from typing import Optional, TYPE_CHECKING
from src.utils.llm import call_llm, LLMMode
from src.classes.actions import get_action_infos_str
from src.classes.typings import ACTION_NAME_PARAMS_PAIR

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar
    from src.classes.core.world import World


async def parse_player_command(command: str, world: "World", avatar: "Avatar") -> Optional[ACTION_NAME_PARAMS_PAIR]:
    """
    将玩家的自然语言指令解析为 (action_name, params) 元组。
    
    Returns:
        (action_name, params) 或 None（无法解析）
    """
    action_infos = get_action_infos_str(avatar)
    
    region_name = "未知"
    if avatar.tile and hasattr(avatar.tile, 'region'):
        region_name = avatar.tile.region.name
    
    prompt = (
        f"你是一个修仙世界的动作解析器。\n\n"
        f"当前玩家角色：{avatar.name}\n"
        f"当前境界：{avatar.cultivation_progress.realm}\n"
        f"所在位置：{region_name}\n\n"
        f"可用的动作列表（JSON格式）：\n"
        f"{action_infos}\n\n"
        f"请将玩家的自然语言指令解析为动作。"
        f"只返回一个 JSON 对象，不要有其他内容：\n"
        f'{{"action_name": "动作类名", "params": {{"param_name": "参数值"}}}}\n\n'
        f"如果玩家指令不明确或缺少参数，返回空对象 {{}}。"
        f"如果玩家想做的事无法用现有动作实现，返回空对象 {{}}。"
        f"如果有多重意图，只选最核心的一个。\n\n"
        f"玩家指令：{command}"
    )

    try:
        response = await call_llm(prompt, mode=LLMMode.NORMAL)
        
        # 尝试解析 JSON
        text = response.strip()
        # 移除可能的 markdown 代码块
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        
        result = json.loads(text)
        
        if not result:
            return None
        
        action_name = result.get("action_name")
        params = result.get("params", {}) or {}
        
        if not action_name:
            return None
        
        return (action_name, params)
        
    except (json.JSONDecodeError, Exception) as e:
        print(f"[PlayerCommandParser] 解析失败: {e}")
        return None


def validate_and_fill_params(action_name: str, params: dict, world: "World", avatar: "Avatar") -> tuple[bool, str]:
    """
    验证并补全动作参数。
    
    Returns:
        (success, error_message)
    """
    from src.classes.action.registry import ActionRegistry
    
    if action_name not in ActionRegistry.all_names():
        return False, f"未知动作: {action_name}"
    
    action_cls = ActionRegistry.get(action_name)
    if not action_cls:
        return False, f"无法找到动作类: {action_name}"
    
    # 检查动作是否可执行
    action_inst = action_cls(avatar, world)
    
    # 检查必要参数
    if hasattr(action_cls, 'PARAMS'):
        for param_name in action_cls.PARAMS:
            if param_name not in params or not params[param_name]:
                return False, f"缺少参数: {param_name}"
    
    # 尝试 can_start
    try:
        can_start_result = action_inst.can_start(**params) if params else action_inst.can_start()
        if isinstance(can_start_result, tuple):
            ok, msg = can_start_result
            if not ok:
                return False, msg
        elif not can_start_result:
            return False, "动作无法执行"
    except Exception as e:
        return False, f"参数验证失败: {e}"
    
    return True, ""
