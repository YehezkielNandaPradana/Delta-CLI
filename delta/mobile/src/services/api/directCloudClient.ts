import { useSettingsStore } from '../../store/useSettingsStore';
import { ChatResponse } from './chatApi';

export const DELTA_SYSTEM_PROMPT = `Delta is an AI-powered Cyber Security Assessment CLI & Mobile Assistant.
You specialize in network security analysis, vulnerability evaluation, scanning workflows, web exploitation mitigation, reconnaissance, and offensive/defensive cybersecurity guidance.
Respond concisely, cleanly, with clear actionable technical advice and cybersecurity insights.`;

export interface ChatMessagePayload {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface DirectChatCompletionPayload {
  model: string;
  messages: ChatMessagePayload[];
  temperature?: number;
  max_tokens?: number;
  stream?: boolean;
}

export function formatDirectChatPayload(
  message: string,
  model: string,
  history: ChatMessagePayload[] = []
): DirectChatCompletionPayload {
  return {
    model: model || 'gemini-1.5-flash',
    messages: [
      { role: 'system', content: DELTA_SYSTEM_PROMPT },
      ...history,
      { role: 'user', content: message },
    ],
    temperature: 0.7,
    stream: false,
  };
}

const FALLBACK_GEMINI_MODELS = [
  'gemini-1.5-flash',
  'gemini-1.5-flash-latest',
  'gemini-1.5-pro',
  'gemini-1.5-pro-latest',
  'gemini-3.6-flash',
];

/**
 * Handle direct Google Gemini REST API with automatic high-demand fallback
 */
async function callGoogleGeminiApi(
  apiKey: string,
  modelName: string,
  message: string
): Promise<ChatResponse> {
  let cleanModel = modelName.replace(/^(ag|google|antigravity)\//i, '');
  if (!cleanModel || cleanModel.toLowerCase().includes('combo') || cleanModel.includes('3.7-flash-high')) {
    cleanModel = 'gemini-1.5-flash';
  }

  // Model chain: requested model first, then standard fallbacks
  const candidateModels = [
    cleanModel,
    ...FALLBACK_GEMINI_MODELS.filter((m) => m !== cleanModel),
  ];

  let lastError = '';

  for (const targetModel of candidateModels) {
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${targetModel}:generateContent?key=${apiKey.trim()}`;

    const payload = {
      system_instruction: {
        parts: [{ text: DELTA_SYSTEM_PROMPT }],
      },
      contents: [
        {
          role: 'user',
          parts: [{ text: message }],
        },
      ],
      generationConfig: {
        temperature: 0.7,
        maxOutputTokens: 2048,
      },
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 25000);

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!res.ok) {
        let errMsg = `Google Gemini Error (${res.status})`;
        try {
          const errJson = await res.json();
          if (errJson.error?.message) {
            errMsg = errJson.error.message;
          }
        } catch (_) {}

        lastError = errMsg;

        // If 503 / high demand / model not found, try next candidate model
        if (
          res.status === 503 ||
          res.status === 404 ||
          errMsg.toLowerCase().includes('demand') ||
          errMsg.toLowerCase().includes('not found') ||
          errMsg.toLowerCase().includes('quota')
        ) {
          continue;
        }
        throw new Error(errMsg);
      }

      const data = await res.json();
      const replyText = data.candidates?.[0]?.content?.parts?.[0]?.text || '';

      if (!replyText) {
        if (data.promptFeedback?.blockReason) {
          throw new Error(`Google AI Blocked: ${data.promptFeedback.blockReason}`);
        }
        continue;
      }

      return {
        output: replyText,
        response: replyText,
        is_task: false,
        task_id: null,
      };
    } catch (err: any) {
      clearTimeout(timeoutId);
      if (err.name === 'AbortError') {
        lastError = 'Permintaan ke Google Gemini timed out.';
        continue;
      }
      lastError = err.message;
    }
  }

  throw new Error(`Google AI: ${lastError}`);
}

/**
 * Handle OpenAI-compatible endpoints (Antigravity Gateway / Custom Proxy)
 */
async function callOpenAICompatibleApi(
  baseUrl: string,
  apiKey: string,
  modelName: string,
  message: string
): Promise<ChatResponse> {
  const cleanBaseUrl = (baseUrl || 'https://api.antigravity.ai/v1').replace(/\/+$/, '');
  const url = `${cleanBaseUrl}/chat/completions`;
  const payload = formatDirectChatPayload(message, modelName);

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 35000);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey.trim()}`,
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      let errorMsg = `Cloud Gateway Error (${response.status})`;
      try {
        const errorJson = await response.json();
        if (errorJson.error?.message) {
          errorMsg = errorJson.error.message;
        } else if (errorJson.message) {
          errorMsg = errorJson.message;
        }
      } catch (_) {}
      throw new Error(errorMsg);
    }

    const data = await response.json();
    const replyText =
      data.choices?.[0]?.message?.content ||
      data.response ||
      data.output ||
      '';

    return {
      output: replyText,
      response: replyText,
      is_task: false,
      task_id: null,
    };
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === 'AbortError') {
      throw new Error('Permintaan ke Cloud Gateway timed out. Periksa koneksi internet Anda.');
    }
    throw err;
  }
}

export async function sendDirectCloudMessage(
  message: string,
  executionId?: string
): Promise<ChatResponse> {
  const store = useSettingsStore.getState();
  const activeAccount = store.getActiveAccount();

  if (!activeAccount) {
    throw new Error('Tidak ada akun yang aktif. Buka Settings dan tambahkan akun.');
  }

  const rawKey = (activeAccount.apiKey || '').trim();
  if (!rawKey) {
    throw new Error(
      `Akun "${activeAccount.name}" belum memiliki API Key. Buka menu Settings dan masukkan API Key.`
    );
  }

  const selectedModel =
    store.cloudModel || activeAccount.defaultModel || 'gemini-1.5-flash';
  const customUrl = (activeAccount.baseUrl || '').trim();

  // Jika Base URL kosong ATAU API Key diawali AIzaSy ATAU URL mengarah ke googleapis
  const isGoogle =
    !customUrl ||
    rawKey.startsWith('AIzaSy') ||
    customUrl.toLowerCase().includes('googleapis.com');

  if (isGoogle) {
    return callGoogleGeminiApi(rawKey, selectedModel, message);
  }

  return callOpenAICompatibleApi(
    customUrl,
    rawKey,
    selectedModel,
    message
  );
}
