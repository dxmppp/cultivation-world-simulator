"""
降服动作

在战斗后将弱势敌人收为随从。
条件：目标当前 HP <= 最大 HP 的 30%
成功率：基于境界差、魅力、当前态势
"""
from __future__ import annotations
import random
from typing import TYPE_CHECKING

from src.i18n import t
from src.classes.action import InstantAction
from src.classes.action.targeting_mixin import TargetingMixin
from src.classes.event import Event

if TYPE_CHECKING:
    from src.classes.core.avatar import Avatar


class Subdue(InstantAction, TargetingMixin):
    """
    降服：战后收对手为随从。
    条件：目标 HP <= HP上限的30%
    """
    
    ACTION_NAME_ID = "subdue_action_name"
    DESC_ID = "subdue_description"
    REQUIREMENTS_ID = "subdue_requirements"
    
    EMOJI = "🔒"
    PARAMS = {"avatar_name": "AvatarName"}
    IS_MAJOR: bool = True
    
    # 降服成功率基础值
    BASE_SUCCESS_RATE = 0.5
    
    def _calc_success_rate(self, target: "Avatar") -> float:
        """计算降服成功率"""
        # 基础成功率
        rate = self.BASE_SUCCESS_RATE
        
        # 境界差修正：境界越高，降服成功率越高
        player_realm_level = self.avatar.cultivation_progress.level
        target_realm_level = target.cultivation_progress.level
        realm_diff = player_realm_level - target_realm_level
        rate += realm_diff * 0.05  # 每低一阶降低5%，高一阶增加5%
        
        # HP 越低越容易降服
        hp_ratio = target.hp.current / target.hp.max_val
        rate += (0.3 - hp_ratio) * 0.5  # HP越低加成越高
        
        # 魅力修正（如果有魅力属性）
        if hasattr(self.avatar, 'appearance_level'):
            charm = getattr(self.avatar, 'appearance_level', 5)
            rate += (charm - 5) * 0.02  # 颜值高于均值有加成
        
        # 上下限
        return max(0.1, min(0.95, rate))
    
    def _execute(self, avatar_name: str) -> None:
        from src.classes.core.avatar import Avatar
        from src.classes.relation.relation import RelationState, Relation
        
        target = resolve_query(avatar_name, self.world, expected_types=[Avatar]).obj
        if target is None:
            self._last_result = None
            return
        
        # 计算成功率
        success_rate = self._calc_success_rate(target)
        roll = random.random()
        success = roll < success_rate
        
        if success:
            # 收为随从
            self.avatar.add_subordinate(target.id)
            target.master_id = self.avatar.id
            # 同时增加好感度
            self.avatar.add_friend(target.id)
            self._last_result = ("success", target, success_rate)
        else:
            # 降服失败，对手可能逃跑或反击
            self._last_result = ("failed", target, success_rate)

    def can_start(self, avatar_name: str) -> tuple[bool, str]:
        if not avatar_name:
            return False, t("Missing target parameter")
            
        from src.classes.core.avatar import Avatar
        target = resolve_query(avatar_name, self.world, expected_types=[Avatar]).obj
        if target is None:
            return False, t("Target does not exist")
        if target.is_dead:
            return False, t("Target is already dead")
        if target.master_id is not None:
            return False, t("Target already has a master")
        if self.avatar.id == target.id:
            return False, t("Cannot subdue yourself")
        
        # HP 门槛：目标 HP <= HP上限的30%
        hp_ratio = target.hp.current / target.hp.max_val if target.hp.max_val > 0 else 0
        if hp_ratio > 0.3:
            return False, t("Target HP is too high, weaken them first (need <= 30%)")
        
        return True, ""

    def start(self, avatar_name: str) -> Event:
        from src.classes.core.avatar import Avatar
        target = resolve_query(avatar_name, self.world, expected_types=[Avatar]).obj
        target_name = target.name if target is not None else avatar_name
        
        rate = self._calc_success_rate(target) if target else 0.5
        
        rel_ids = [self.avatar.id]
        if target is not None:
            rel_ids.append(target.id)
            
        content = t("{attacker} attempts to subdue {target}",
                   attacker=self.avatar.name, target=target_name)
        event = Event(
            self.world.month_stamp, 
            content, 
            related_avatars=rel_ids, 
            is_major=True
        )
        self._start_event_content = event.content
        return event

    def finish(self, avatar_name: str) -> list[Event]:
        from src.classes.event import Event
        from src.classes.core.avatar import Avatar
        
        result = self._last_result
        if not result:
            return []
        
        status, target, rate = result
        start_text = getattr(self, '_start_event_content', "")
        
        if status == "success":
            content = t("{player} successfully subdued {target}! {target} is now a subordinate.",
                       player=self.avatar.name, target=target.name)
            event = Event(
                self.world.month_stamp,
                content,
                related_avatars=[self.avatar.id, target.id],
                is_major=True,
                event_type="subdue_success",
                render_params={
                    "subject_name": target.name,
                }
            )
        else:
            content = t("{player} failed to subdue {target}. {target} breaks free!",
                       player=self.avatar.name, target=target.name)
            event = Event(
                self.world.month_stamp,
                content,
                related_avatars=[self.avatar.id, target.id],
                is_major=False,
                event_type="subdue_failed",
                render_params={
                    "subject_name": target.name,
                }
            )
        
        return [event]


# 注意：resolve_query 在这里需要导入，但 TargetingMixin 已经做了
# 只需要确保正确解析
from src.utils.resolution import resolve_query
