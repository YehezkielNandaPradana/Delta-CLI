import { useSettingsStore } from '../../store/useSettingsStore';

export interface TelegramUser {
  id: number;
  is_bot: boolean;
  first_name: string;
  username?: string;
}

export interface TelegramSendMessageResponse {
  ok: boolean;
  result?: {
    message_id: number;
    chat: {
      id: number;
      type: string;
      title?: string;
      username?: string;
    };
    date: number;
    text: string;
  };
  description?: string;
  error_code?: number;
}

export interface TelegramUpdate {
  update_id: number;
  message?: {
    message_id: number;
    from: TelegramUser;
    chat: {
      id: number;
      type: string;
      title?: string;
      username?: string;
    };
    date: number;
    text?: string;
  };
}

class HermesTelegramService {
  private getBaseUrl(token?: string): string {
    const activeToken = token || useSettingsStore.getState().telegramBotToken;
    return `https://api.telegram.org/bot${activeToken.trim()}`;
  }

  /**
   * Test Telegram bot token by calling getMe
   */
  async testBot(token?: string): Promise<{ success: boolean; bot?: TelegramUser; error?: string }> {
    const activeToken = (token || useSettingsStore.getState().telegramBotToken).trim();
    if (!activeToken) {
      return { success: false, error: 'Token Bot Telegram belum diisi.' };
    }

    try {
      const res = await fetch(`https://api.telegram.org/bot${activeToken}/getMe`);
      const data = await res.json();
      if (data.ok && data.result) {
        return { success: true, bot: data.result as TelegramUser };
      }
      return {
        success: false,
        error: data.description || `Telegram Error (${data.error_code || res.status})`,
      };
    } catch (err: any) {
      return {
        success: false,
        error: err.message || 'Gagal menghubungi Telegram API (periksa jaringan internet).',
      };
    }
  }

  /**
   * Send a text message to the configured or specified Telegram Chat ID
   */
  async sendMessage(
    text: string,
    options?: {
      chatId?: string;
      token?: string;
      parseMode?: 'Markdown' | 'HTML';
    }
  ): Promise<{ success: boolean; messageId?: number; error?: string }> {
    const token = (options?.token || useSettingsStore.getState().telegramBotToken).trim();
    const chatId = (options?.chatId || useSettingsStore.getState().telegramChatId).trim();

    if (!token) {
      return { success: false, error: 'Token Telegram Bot belum dikonfigurasi.' };
    }
    if (!chatId) {
      return { success: false, error: 'Chat ID Telegram belum ditentukan.' };
    }

    try {
      const url = `https://api.telegram.org/bot${token}/sendMessage`;
      const bodyPayload: any = {
        chat_id: chatId,
        text: text,
      };
      if (options?.parseMode) {
        bodyPayload.parse_mode = options.parseMode;
      }

      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyPayload),
      });

      const data: TelegramSendMessageResponse = await res.json();
      if (data.ok && data.result) {
        return { success: true, messageId: data.result.message_id };
      }

      // If Markdown fails, fallback to sending plain text
      if (options?.parseMode) {
        return this.sendMessage(text, { ...options, parseMode: undefined });
      }

      return {
        success: false,
        error: data.description || `HTTP ${res.status}`,
      };
    } catch (err: any) {
      return {
        success: false,
        error: err.message || 'Koneksi ke Telegram gagal.',
      };
    }
  }

  /**
   * Send a note formatted nicely to Telegram Hermes Bot
   */
  async sendNote(note: { title: string; content: string; tags?: string[] }): Promise<{ success: boolean; error?: string }> {
    const tagList = note.tags && note.tags.length > 0 ? note.tags.map((t) => `#${t.replace(/\s+/g, '_')}`).join(' ') : '';
    const formatted = `📝 *Delta Note Export*\n\n📌 *${note.title}*\n\n${note.content}\n\n${tagList ? `${tagList}\n` : ''}_Sent from Delta Mobile_`;
    return this.sendMessage(formatted, { parseMode: 'Markdown' });
  }

  /**
   * Send a chat message / AI finding alert to Telegram
   */
  async sendAlert(title: string, message: string): Promise<{ success: boolean; error?: string }> {
    const formatted = `🛡️ *Delta Alert: ${title}*\n\n${message}\n\n_Delta Mobile Engine_`;
    return this.sendMessage(formatted, { parseMode: 'Markdown' });
  }

  /**
   * Poll updates from Telegram (for 2-way bot messaging if needed)
   */
  async getUpdates(offset?: number, token?: string): Promise<{ success: boolean; updates?: TelegramUpdate[]; error?: string }> {
    const activeToken = (token || useSettingsStore.getState().telegramBotToken).trim();
    if (!activeToken) return { success: false, error: 'Token belum diisi' };

    try {
      const url = `https://api.telegram.org/bot${activeToken}/getUpdates?timeout=5${offset ? `&offset=${offset}` : ''}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.ok && Array.isArray(data.result)) {
        return { success: true, updates: data.result };
      }
      return { success: false, error: data.description };
    } catch (err: any) {
      return { success: false, error: err.message };
    }
  }
  /**
   * Send chat prompt directly to Hermes Bot and wait for reply via Telegram getUpdates
   */
  async chatWithHermes(prompt: string, timeoutMs: number = 20000): Promise<{ success: boolean; response?: string; error?: string }> {
    const token = useSettingsStore.getState().telegramBotToken.trim();
    const chatId = useSettingsStore.getState().telegramChatId.trim();

    if (!token) {
      return { success: false, error: 'Telegram Bot Token belum diisi di menu Settings > Hermes Bot Telegram.' };
    }
    if (!chatId) {
      return { success: false, error: 'Telegram Chat ID belum diisi di menu Settings > Hermes Bot Telegram.' };
    }

    // 1. Ambil update terbaru untuk tracking update_id
    let latestUpdateId = 0;
    try {
      const initialUpdates = await this.getUpdates(undefined, token);
      if (initialUpdates.success && initialUpdates.updates && initialUpdates.updates.length > 0) {
        latestUpdateId = initialUpdates.updates[initialUpdates.updates.length - 1].update_id + 1;
      }
    } catch (_) {}

    // 2. Kirim prompt ke Telegram chat Hermes bot
    const sendRes = await this.sendMessage(prompt, { chatId, token });
    if (!sendRes.success) {
      return { success: false, error: sendRes.error || 'Gagal mengirim pesan ke Telegram bot.' };
    }

    // 3. Polling balasan bot selama timeoutMs
    const startTime = Date.now();
    let currentOffset = latestUpdateId;

    while (Date.now() - startTime < timeoutMs) {
      await new Promise((r) => setTimeout(r, 1200));
      const pollRes = await this.getUpdates(currentOffset, token);

      if (pollRes.success && pollRes.updates && pollRes.updates.length > 0) {
        for (const update of pollRes.updates) {
          currentOffset = update.update_id + 1;
          const msg = update.message;
          if (msg && msg.text) {
            const isTargetChat = String(msg.chat.id) === chatId;
            // Deteksi pesan jawaban dari bot (atau dari akun chat jika bot bertindak sebagai webhook/userbot)
            if (isTargetChat && msg.message_id !== sendRes.messageId) {
              return {
                success: true,
                response: msg.text,
              };
            }
          }
        }
      }
    }

    return {
      success: true,
      response: `✓ Prompt terkirim ke Telegram Hermes Bot (Pesan ID: ${sendRes.messageId}).\n\nJika Hermes Bot Anda memproses di background, respons akan muncul di aplikasi Telegram Anda.`,
    };
  }
}

export const hermesTelegramService = new HermesTelegramService();
