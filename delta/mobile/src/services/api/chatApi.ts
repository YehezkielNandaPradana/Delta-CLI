import { apiRequest } from './apiClient';
import { useSettingsStore } from '../../store/useSettingsStore';
import { embedded9Router } from '../router/embeddedRouterEngine';
import { noteAgentBridge } from '../notes/noteAgentBridge';
import { useReminderStore } from '../../store/useReminderStore';
import { hermesTelegramService } from '../telegram/hermesTelegramService';

export interface ChatResponse {
  output?: string;
  response?: string;
  is_task?: boolean;
  task_id?: string | null;
  error?: string;
}

/**
 * Parses and executes embedded note & reminder creation directives from LLM responses
 */
async function processEmbeddedActions(rawText: string): Promise<string> {
  if (!rawText) return rawText;

  let cleanText = rawText;

  // 1. Process Notes
  if (cleanText.includes('[DELTA_CREATE_NOTE:')) {
    const noteRegex = /\[DELTA_CREATE_NOTE:\s*({[\s\S]*?})\]/g;
    let match: RegExpExecArray | null;
    const createdNotes: string[] = [];

    while ((match = noteRegex.exec(rawText)) !== null) {
      try {
        const payload = JSON.parse(match[1]);
        if (payload.title || payload.content) {
          const res = await noteAgentBridge.createNote({
            title: payload.title || 'Catatan Baru',
            content: payload.content || '',
            tags: Array.isArray(payload.tags) ? payload.tags : ['Agent'],
          });
          if (res.success) {
            createdNotes.push(payload.title || 'Catatan');
          }
        }
      } catch (_) {}
    }

    cleanText = cleanText.replace(/\[DELTA_CREATE_NOTE:\s*{[\s\S]*?}\]/g, '').trim();
    if (createdNotes.length > 0) {
      cleanText = `${cleanText}\n\n📝 *Tersimpan ke Delta Note:* "${createdNotes.join(', ')}"`;
    }
  }

  // 2. Process Reminders
  if (cleanText.includes('[DELTA_CREATE_REMINDER:')) {
    const reminderRegex = /\[DELTA_CREATE_REMINDER:\s*({[\s\S]*?})\]/g;
    let rMatch: RegExpExecArray | null;
    const createdReminders: string[] = [];

    while ((rMatch = reminderRegex.exec(rawText)) !== null) {
      try {
        const rPayload = JSON.parse(rMatch[1]);
        if (rPayload.title) {
          const delay = typeof rPayload.delayMinutes === 'number' ? rPayload.delayMinutes : 1;
          await useReminderStore.getState().createReminder({
            title: rPayload.title,
            delayMinutes: delay,
            note: rPayload.note || '',
          });
          createdReminders.push(`${rPayload.title} (${delay} menit lagi)`);
        }
      } catch (_) {}
    }

    cleanText = cleanText.replace(/\[DELTA_CREATE_REMINDER:\s*{[\s\S]*?}\]/g, '').trim();
    if (createdReminders.length > 0) {
      cleanText = `${cleanText}\n\n🔔 *Pengingat Diaktifkan:* "${createdReminders.join(', ')}"`;
    }
  }

  return cleanText;
}

export async function sendChatMessage(
  message: string,
  executionId?: string
): Promise<ChatResponse> {
  const { connectionMode, cloudModel, activeModel, getActiveAccount, activeAgent } = useSettingsStore.getState();

  let result: ChatResponse;

  if (connectionMode === 'telegram') {
    // Mode Eksklusif Telegram: hanya menghubungi Telegram Hermes Bot
    const tgRes = await hermesTelegramService.chatWithHermes(message);
    if (tgRes.success) {
      result = {
        response: tgRes.response || 'Pesan terkirim ke Telegram Hermes Bot.',
      };
    } else {
      result = {
        error: tgRes.error || 'Gagal berkomunikasi dengan Telegram Hermes Bot.',
      };
    }
  } else if (connectionMode === 'cloud') {
    const defaultModel = activeAgent === 'nazza' ? 'AntigravityCombo' : 'ag/gemini-3.7-flash-high';
    const selectedModel = cloudModel || activeModel || defaultModel;
    const activeAccount = getActiveAccount();
    result = await embedded9Router.routeCompletion(message, selectedModel, activeAccount);
  } else {
    result = await apiRequest<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        command: message,
        prompt: message,
        message: message,
        execution_id: executionId,
      }),
    });
  }

  // Intercept & handle auto-note & reminder directives once
  const rawText = result.response || result.output || '';
  if (rawText && (rawText.includes('[DELTA_CREATE_NOTE:') || rawText.includes('[DELTA_CREATE_REMINDER:'))) {
    const processed = await processEmbeddedActions(rawText);
    if (result.response) result.response = processed;
    if (result.output) result.output = processed;
  }

  // Auto-forward to Telegram Hermes Bot if configured and enabled
  const finalOutput = result.response || result.output || '';
  const { telegramAutoForward, telegramBotToken } = useSettingsStore.getState();
  if (telegramAutoForward && telegramBotToken && finalOutput && !result.error) {
    hermesTelegramService.sendMessage(
      `🤖 *Delta AI Response*\n\n_Prompt:_ ${message.slice(0, 100)}\n\n${finalOutput}`,
      { parseMode: 'Markdown' }
    ).catch(() => {});
  }

  return result;
}

export async function cancelExecution(): Promise<{ status: string; message?: string }> {
  const { connectionMode } = useSettingsStore.getState();
  if (connectionMode === 'cloud') {
    return { status: 'cancelled', message: 'Direct request aborted' };
  }

  return apiRequest<{ status: string; message?: string }>('/api/cancel', {
    method: 'POST',
  });
}
