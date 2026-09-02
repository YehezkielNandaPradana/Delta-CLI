import { useSettingsStore } from '../../store/useSettingsStore';
import { useSkillsStore } from '../../store/useSkillsStore';
import { ChatResponse } from './chatApi';

export const DELTA_SYSTEM_PROMPT = `Delta is an AI-powered Cyber Security Assessment CLI & Mobile Assistant.
You specialize in network security analysis, vulnerability evaluation, scanning workflows, web exploitation mitigation, reconnaissance, and offensive/defensive cybersecurity guidance.
Respond concisely, cleanly, with clear actionable technical advice and cybersecurity insights.

NOTE CREATION CAPABILITY:
When the user asks or commands to take a note, write a note, save findings, or summarize something into notes (e.g., "buatkan catatan...", "catat bahwa...", "simpan ini ke catatan", "make a note about..."), you MUST output a special JSON action tag at the beginning or end of your response in this exact format:
[DELTA_CREATE_NOTE: {"title": "Short Descriptive Title", "content": "Full detailed note markdown content here", "tags": ["tag1", "tag2"]}]
Always provide a friendly explanation in plain text along with the tag confirming that the note has been saved.

REMINDER / NOTIFICATION CAPABILITY:
When the user asks to remind them or set an alarm/reminder (e.g., "ingatkan saya 5 menit lagi untuk...", "buatkan pengingat...", "remind me in 10 minutes to..."), you MUST output a special JSON action tag in this exact format:
[DELTA_CREATE_REMINDER: {"title": "Short Reminder Title", "delayMinutes": 5, "note": "Detailed context or description"}]
Always confirm in conversational text that the reminder has been set.`;

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
  const dynamicSkillContext = useSkillsStore.getState().getActiveSkillPrompts(message);
  const fullSystemPrompt = `${DELTA_SYSTEM_PROMPT}${dynamicSkillContext}`;

  return {
    model: model || 'gemini-1.5-flash',
    messages: [
      { role: 'system', content: fullSystemPrompt },
      ...history,
      { role: 'user', content: message },
    ],
    temperature: 0.7,
    stream: false,
  };
}

export const KNOWN_GOOGLE_MODELS = [
  'gemini-1.5-pro',
  'gemini-2.0-flash',
  'gemini-1.5-flash',
  'gemini-1.5-pro-latest',
  'gemini-1.5-flash-latest',
];

/**
 * Fetch available Google Gemini models directly via API Key
 */
export async function testAndFetchGoogleModels(apiKey: string): Promise<{
  success: boolean;
  models: string[];
  tier: 'pro' | 'flash' | 'standard';
  bestModel: string;
  error?: string;
}> {
  const cleanKey = apiKey.trim();
  if (!cleanKey) {
    return {
      success: false,
      models: [],
      tier: 'standard',
      bestModel: 'gemini-1.5-flash',
      error: 'API Key kosong',
    };
  }

  try {
    const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${cleanKey}`;
    const res = await fetch(url);
    if (!res.ok) {
      let errMsg = `Status ${res.status}`;
      try {
        const json = await res.json();
        if (json.error?.message) errMsg = json.error.message;
      } catch (_) {}
      return {
        success: false,
        models: [],
        tier: 'standard',
        bestModel: 'gemini-1.5-flash',
        error: errMsg,
      };
    }

    const data = await res.json();
    const rawList: any[] = data.models || [];
    const modelNames = rawList
      .map((m) => m.name?.replace(/^models\//, ''))
      .filter((n) => typeof n === 'string' && n.includes('gemini'));

    const hasPro = modelNames.some((n) => n.includes('pro'));
    const tier = hasPro ? 'pro' : 'flash';

    // Pick best default model
    let bestModel = 'gemini-1.5-flash';
    if (modelNames.includes('gemini-1.5-pro')) {
      bestModel = 'gemini-1.5-pro';
    } else if (modelNames.includes('gemini-2.0-flash')) {
      bestModel = 'gemini-2.0-flash';
    } else if (modelNames.length > 0) {
      bestModel = modelNames[0];
    }

    return {
      success: true,
      models: modelNames.length > 0 ? modelNames : KNOWN_GOOGLE_MODELS,
      tier,
      bestModel,
    };
  } catch (err: any) {
    return {
      success: false,
      models: [],
      tier: 'standard',
      bestModel: 'gemini-1.5-flash',
      error: err.message || 'Koneksi ke Google AI Studio gagal',
    };
  }
}

/**
 * Handle direct Google Gemini REST API with fallback
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

  const candidateModels = [
    cleanModel,
    ...KNOWN_GOOGLE_MODELS.filter((m) => m !== cleanModel),
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
    throw new Error('Tidak ada akun yang aktif. Buka Settings dan sambungkan akun Google AI atau Antigravity.');
  }

  const rawKey = (activeAccount.apiKey || '').trim();
  if (!rawKey) {
    throw new Error(
      `Akun "${activeAccount.name}" belum memiliki API Key. Buka menu Settings dan hubungkan akun Google AI.`
    );
  }

  const selectedModel =
    store.cloudModel || activeAccount.defaultModel || 'gemini-1.5-flash';
  const customUrl = (activeAccount.baseUrl || '').trim();

  const isGoogle =
    activeAccount.accountType === 'google' ||
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
