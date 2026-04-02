<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { NInput, NInputNumber, NButton, NCard, NSpace, NTag, NSpin, NEmpty, NDivider, NSelect } from 'naive-ui';
import { playerApi, type PlayerStatusDTO } from '../../../api';

const { t } = useI18n();

const props = defineProps<{
  gameInitialized: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

// 状态
const players = ref<{ id: string; name: string; realm: string }[]>([]);
const selectedPlayerId = ref<string | null>(null);
const playerStatus = ref<PlayerStatusDTO | null>(null);
const commandInput = ref('');
const commandResult = ref<{ ok: boolean; message: string } | null>(null);
const loading = ref(false);
const statusLoading = ref(false);
const error = ref<string | null>(null);

// 创建新角色
const showCreateForm = ref(false);
const newPlayerName = ref('');
const newPlayerGender = ref('男');
const newPlayerAge = ref(18);
const newPlayerRealm = ref('Mortal');
const creatingPlayer = ref(false);

// 轮询状态
let statusPollInterval: ReturnType<typeof setInterval> | null = null;

// 加载玩家列表
async function loadPlayers() {
  try {
    const res = await playerApi.listPlayers();
    players.value = res.players;
    if (players.value.length > 0 && !selectedPlayerId.value) {
      selectPlayer(players.value[0].id);
    }
  } catch (e) {
    error.value = '加载玩家列表失败';
    console.error(e);
  }
}

// 选择玩家
async function selectPlayer(id: string) {
  selectedPlayerId.value = id;
  await loadPlayerStatus();
}

// 加载玩家状态
async function loadPlayerStatus() {
  if (!selectedPlayerId.value) return;
  
  statusLoading.value = true;
  try {
    const res = await playerApi.getPlayerStatus(selectedPlayerId.value);
    playerStatus.value = res;
    error.value = null;
  } catch (e) {
    error.value = '加载状态失败';
    console.error(e);
  } finally {
    statusLoading.value = false;
  }
}

// 发送指令
async function submitCommand() {
  if (!commandInput.value.trim() || !selectedPlayerId.value) return;
  
  loading.value = true;
  commandResult.value = null;
  
  try {
    const res = await playerApi.submitCommand({
      player_avatar_id: selectedPlayerId.value,
      command: commandInput.value.trim(),
    });
    
    if (res.status === 'ok') {
      commandResult.value = { ok: true, message: res.message || '指令已发送' };
      commandInput.value = '';
    } else {
      commandResult.value = { ok: false, message: res.message || '指令执行失败' };
    }
    
    // 刷新状态
    await loadPlayerStatus();
  } catch (e) {
    commandResult.value = { ok: false, message: '发送失败: ' + (e as Error).message };
  } finally {
    loading.value = false;
  }
}

// 启动状态轮询
function startStatusPoll() {
  if (statusPollInterval) return;
  statusPollInterval = setInterval(() => {
    if (selectedPlayerId.value) {
      loadPlayerStatus();
    }
  }, 5000); // 每5秒刷新一次
}

// 停止状态轮询
function stopStatusPoll() {
  if (statusPollInterval) {
    clearInterval(statusPollInterval);
    statusPollInterval = null;
  }
}

onMounted(() => {
  if (props.gameInitialized) {
    loadPlayers();
    startStatusPoll();
  }
});

onUnmounted(() => {
  stopStatusPoll();
});

// 创建新玩家角色
async function createPlayer() {
  if (!newPlayerName.value.trim()) return;
  
  creatingPlayer.value = true;
  try {
    const res = await playerApi.createPlayer({
      name: newPlayerName.value.trim(),
      gender: newPlayerGender.value,
      age: newPlayerAge.value,
      initial_realm: newPlayerRealm.value,
    });
    
    if (res.status === 'ok') {
      showCreateForm.value = false;
      newPlayerName.value = '';
      newPlayerAge.value = 18;
      await loadPlayers();
      selectPlayer(res.avatar_id);
    }
  } catch (e) {
    error.value = '创建失败: ' + (e as Error).message;
  } finally {
    creatingPlayer.value = false;
  }
}

const realmLabel = computed(() => {
  if (!playerStatus.value) return '';
  const realmMap: Record<string, string> = {
    Mortal: '凡人',
    Qi_Refinement: '练气',
    Foundation_Establishment: '筑基',
    Core_Formation: '金丹',
    Nascent_Soul: '元婴',
    Spirit_Transformation: '化神',
    Resonance: '合体',
    Void_Return: '大乘',
    Tribulation: '渡劫',
    Immortal: '真仙',
  };
  return realmMap[playerStatus.value.realm] || playerStatus.value.realm;
});

const realmOptions = [
  { label: '凡人 (Mortal)', value: 'Mortal' },
  { label: '练气 (Qi Refinement)', value: 'Qi_Refinement' },
  { label: '筑基 (Foundation Establishment)', value: 'Foundation_Establishment' },
  { label: '金丹 (Core Formation)', value: 'Core_Formation' },
  { label: '元婴 (Nascent Soul)', value: 'Nascent_Soul' },
  { label: '化神 (Spirit Transformation)', value: 'Spirit_Transformation' },
  { label: '合体 (Resonance)', value: 'Resonance' },
  { label: '大乘 (Void Return)', value: 'Void_Return' },
  { label: '渡劫 (Tribulation)', value: 'Tribulation' },
  { label: '真仙 (Immortal)', value: 'Immortal' },
];
</script>

<template>
  <div class="player-panel">
    <div class="panel-header">
      <h3>🎮 玩家控制台</h3>
      <button class="close-btn" @click="emit('close')">×</button>
    </div>

    <div class="panel-content">
      <!-- 未初始化提示 -->
      <NEmpty v-if="!gameInitialized" description="游戏未初始化，请先开始游戏">
        <template #extra>
          <NButton size="small" @click="emit('close')">关闭</NButton>
        </template>
      </NEmpty>

      <template v-else>
        <!-- 玩家列表 -->
        <div class="player-list-section">
          <h4>我的角色</h4>
          <div v-if="players.length === 0 && !showCreateForm" class="no-players">
            <NEmpty description="暂无玩家角色" size="small">
              <template #extra>
                <NButton size="small" type="primary" @click="showCreateForm = true">创建玩家角色</NButton>
              </template>
            </NEmpty>
          </div>
          <div v-else class="player-list">
            <div
              v-for="player in players"
              :key="player.id"
              :class="['player-item', { active: selectedPlayerId === player.id }]"
              @click="selectPlayer(player.id)"
            >
              <span class="player-name">{{ player.name }}</span>
              <span class="player-realm">{{ player.realm }}</span>
            </div>
          </div>

          <!-- 创建角色按钮 -->
          <NButton v-if="!showCreateForm" size="small" block @click="showCreateForm = true" style="margin-top: 8px">
            + 创建玩家角色
          </NButton>

          <!-- 创建角色表单 -->
          <div v-if="showCreateForm" class="create-form">
            <NDivider>创建新角色</NDivider>
            <div class="form-row">
              <span>姓名:</span>
              <NInput v-model:value="newPlayerName" placeholder="输入角色名" size="small" />
            </div>
            <div class="form-row">
              <span>性别:</span>
              <NSelect v-model:value="newPlayerGender" :options="[{label:'男',value:'男'},{label:'女',value:'女'}]" size="small" style="width:100px" />
            </div>
            <div class="form-row">
              <span>年龄:</span>
              <NInputNumber v-model:value="newPlayerAge" :min="1" :max="100" size="small" style="width:100px" />
            </div>
            <div class="form-row">
              <span>境界:</span>
              <NSelect v-model:value="newPlayerRealm" :options="realmOptions" size="small" style="width:180px" />
            </div>
            <div class="form-actions">
              <NButton size="small" @click="showCreateForm = false">取消</NButton>
              <NButton size="small" type="primary" :loading="creatingPlayer" @click="createPlayer">确认创建</NButton>
            </div>
          </div>
        </div>

        <NDivider />

        <!-- 角色状态 -->
        <div v-if="playerStatus" class="player-status">
          <div class="status-header">
            <h4>{{ playerStatus.name }}</h4>
            <NSpin v-if="statusLoading" :size="14" />
          </div>
          
          <div class="status-info">
            <div class="status-row">
              <span class="label">境界:</span>
              <NTag size="small" type="info">{{ realmLabel }}</NTag>
            </div>
            <div class="status-row">
              <span class="label">气血:</span>
              <span>{{ playerStatus.hp }} / {{ playerStatus.hp_max }}</span>
            </div>
            <div class="status-row">
              <span class="label">随从:</span>
              <span>{{ playerStatus.subordinates.length }} 人</span>
            </div>
            <div class="status-row">
              <span class="label">好友:</span>
              <span>{{ playerStatus.friends.length }} 人</span>
            </div>
          </div>

          <!-- 随从列表 -->
          <div v-if="playerStatus.subordinates.length > 0" class="subordinates-section">
            <h5>📜 随从</h5>
            <div class="subordinate-list">
              <div v-for="sub in playerStatus.subordinates" :key="sub.id" class="subordinate-item">
                <span>{{ sub.name }}</span>
                <NTag size="tiny">{{ sub.realm }}</NTag>
              </div>
            </div>
          </div>

          <!-- 好友列表 -->
          <div v-if="playerStatus.friends.length > 0" class="friends-section">
            <h5>🤝 好友</h5>
            <div class="friend-list">
              <div v-for="friend in playerStatus.friends" :key="friend.id" class="friend-item">
                <span>{{ friend.name }}</span>
                <NTag size="tiny" type="warning">{{ friend.realm }}</NTag>
              </div>
            </div>
          </div>
        </div>

        <NDivider />

        <!-- 创建角色按钮 -->
        <NButton v-if="!showCreateForm" size="small" block @click="showCreateForm = true" style="margin-top: 8px">
          + 创建玩家角色
        </NButton>

        <!-- 创建角色表单 -->
        <div v-if="showCreateForm" class="create-form">
          <NDivider>创建新角色</NDivider>
          <div class="form-row">
            <span>姓名:</span>
            <NInput v-model:value="newPlayerName" placeholder="输入角色名" size="small" />
          </div>
          <div class="form-row">
            <span>性别:</span>
            <NSelect v-model:value="newPlayerGender" :options="[{label:'男',value:'男'},{label:'女',value:'女'}]" size="small" style="width:100px" />
          </div>
          <div class="form-row">
            <span>年龄:</span>
            <NInputNumber v-model:value="newPlayerAge" :min="1" :max="100" size="small" style="width:100px" />
          </div>
          <div class="form-row">
            <span>境界:</span>
            <NSelect v-model:value="newPlayerRealm" :options="realmOptions" size="small" style="width:180px" />
          </div>
          <div class="form-actions">
            <NButton size="small" @click="showCreateForm = false">取消</NButton>
            <NButton size="small" type="primary" :loading="creatingPlayer" @click="createPlayer">确认创建</NButton>
          </div>
        </div>

        <!-- 指令输入 -->
        <div class="command-section">
          <h4>💬 发送指令</h4>
          <div class="command-input-area">
            <NInput
              v-model:value="commandInput"
              type="textarea"
              :rows="3"
              :placeholder="`输入指令，如：攻击张三、收服李四、修炼突破`"
              :disabled="loading || !selectedPlayerId"
              @keydown.ctrl.enter="submitCommand"
            />
            <div class="command-hint">
              按 Ctrl+Enter 发送 | 输入自然语言，AI会自动解析为动作
            </div>
          </div>
          
          <NButton
            type="primary"
            block
            :loading="loading"
            :disabled="!commandInput.trim() || !selectedPlayerId"
            @click="submitCommand"
          >
            发送指令
          </NButton>

          <!-- 指令结果 -->
          <div v-if="commandResult" :class="['command-result', commandResult.ok ? 'success' : 'error']">
            {{ commandResult.message }}
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.player-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1a1a2e;
  color: #eee;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #333;
  background: #16213e;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
  padding: 0 4px;
}

.close-btn:hover {
  color: #fff;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.player-list-section h4,
.command-section h4,
.player-status h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #aaa;
}

.no-players {
  padding: 12px;
}

.player-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.player-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #252540;
  border-radius: 6px;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.player-item:hover {
  background: #2d2d4a;
  border-color: #444;
}

.player-item.active {
  background: #2d4a6a;
  border-color: #4a8ac4;
}

.player-name {
  font-weight: 500;
}

.player-realm {
  font-size: 12px;
  color: #888;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.status-header h4 {
  margin: 0;
  font-size: 18px;
  color: #fff;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-row .label {
  color: #888;
  min-width: 50px;
}

.subordinates-section,
.friends-section {
  margin-top: 12px;
}

.subordinates-section h5,
.friends-section h5 {
  margin: 0 0 8px 0;
  font-size: 13px;
  color: #aaa;
}

.subordinate-list,
.friend-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.subordinate-item,
.friend-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 8px;
  background: #252540;
  border-radius: 4px;
  font-size: 13px;
}

.command-input-area {
  margin-bottom: 12px;
}

.command-hint {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
}

.command-result {
  margin-top: 12px;
  padding: 10px;
  border-radius: 6px;
  font-size: 13px;
}

.command-result.success {
  background: rgba(46, 204, 113, 0.15);
  border: 1px solid rgba(46, 204, 113, 0.3);
  color: #2ecc71;
}

.command-result.error {
  background: rgba(231, 76, 60, 0.15);
  border: 1px solid rgba(231, 76, 60, 0.3);
  color: #e74c3c;
}

.create-form {
  margin-top: 12px;
  padding: 12px;
  background: #1e1e38;
  border-radius: 8px;
}

.form-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.form-row span {
  min-width: 50px;
  color: #aaa;
  font-size: 13px;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 12px;
}
</style>
