/**
 * Embedded 9Router Engine for Delta Mobile
 * Provides robust AI model routing across:
 * 1. 9Router Local / Termux Gateway (127.0.0.1:20128, localhost:20128, 10.0.2.2:20128)
 * 2. Google Gemini Official API (Direct AI Studio Key)
 * 3. Antigravity Cloud Gateway
 */

import { Platform } from 'react-native';
import { AntigravityAccount } from '../../types/cloud';
import { ChatResponse } from '../api/chatApi';
import { DELTA_SYSTEM_PROMPT, NAZZA_SYSTEM_PROMPT, KNOWN_GOOGLE_MODELS } from '../api/directCloudClient';
import { useSettingsStore } from '../../store/useSettingsStore';
import { useSkillsStore } from '../../store/useSkillsStore';

export interface EmbeddedRouterStatus {
  running: boolean;
  version: string;
  mode: 'embedded' | 'remote';
  activeProviders: string[];
  activeCombo: string;
  uptime_seconds: number;
}

const startTime = Date.now();

// Candidate host addresses for 9Router local daemon / tunnel
const LOCAL_ROUTER_HOSTS = [
  'https://rurpq7a.abc-tunnel.us/v1',
  'http://192.168.1.6:20128',
  'http://127.0.0.1:20128',
  'http://localhost:20128',
  Platform.OS === 'android' ? 'http://10.0.2.2:20128' : '',
].filter(Boolean);

export class Embedded9Router {
  private static instance: Embedded9Router;
  private isInitialized = false;

  private constructor() {}

  public static getInstance(): Embedded9Router {
    if (!Embedded9Router.instance) {
      Embedded9Router.instance = new Embedded9Router();
    }
    return Embedded9Router.instance;
  }

  public init(): void {
    this.isInitialized = true;
  }

  public getStatus(): EmbeddedRouterStatus {
    return {
      running: true,
      version: '9router-embedded-v2.6',
      mode: 'embedded',
      activeProviders: ['9router-local', 'google', 'antigravity', 'deepseek'],
      activeCombo: 'AntigravityCombo',
      uptime_seconds: Math.floor((Date.now() - startTime) / 1000),
    };
  }

  /**
   * Intelligently route prompt to available provider
   */
  public async routeCompletion(
    message: string,
    modelName: string,
    account?: AntigravityAccount
  ): Promise<ChatResponse> {
    const rawKey = account?.apiKey?.trim() || '';
    const customBaseUrl = (account?.baseUrl || '').trim();

    // 1. Check & Route to Local 9Router (Port 20128 / Tunnel) if live or specified
    const activeLocalHost = await this.findLivePort20128(customBaseUrl, rawKey);
    if (activeLocalHost) {
      try {
        return await this.executeGatewayRoute(message, modelName, `${activeLocalHost}/v1`, rawKey);
      } catch (err: any) {
        // If 9Router port was detected but failed and we have an API Key, fall through
        if (!rawKey) {
          throw new Error(`9Router (Port 20128): ${err.message}`);
        }
      }
    }

    // 2. Custom OpenAI/9Router Cloud Gateway if baseUrl is present
    if (customBaseUrl) {
      return this.executeGatewayRoute(message, modelName, customBaseUrl, rawKey);
    }

    // 3. Google Gemini Direct REST API
    if (rawKey.startsWith('AIzaSy') || account?.accountType === 'google' || rawKey) {
      return this.executeGoogleRoute(message, modelName, rawKey);
    }

    // 4. Fallback attempt to local 9router even without explicit ping success
    const fallbackCandidates = [
      customBaseUrl,
      'http://127.0.0.1:20128/v1',
      'http://localhost:20128/v1',
      'http://192.168.1.6:20128/v1',
    ].filter(Boolean);

    for (const fb of fallbackCandidates) {
      try {
        return await this.executeGatewayRoute(message, modelName, fb, rawKey);
      } catch (_) {}
    }

    // 5. No 9Router daemon & no API key
    throw new Error(
      '9Router gateway (port 20128) belum aktif dan belum ada API Key tersambung.\n\nSolusi Cepat:\n1. Buka Settings → Sambungkan Google AI Studio (Gratis), ATAU\n2. Jalankan 9Router di Termux/PC (port 20128).'
    );
  }

  private async findLivePort20128(customUrl?: string, apiKey?: string): Promise<string | null> {
    const { routerHostUrl, serverUrl } = useSettingsStore.getState();

    // Extract hostname / IP from serverUrl if configured
    let inferredServerHost = '';
    try {
      if (serverUrl && !serverUrl.includes('localhost') && !serverUrl.includes('127.0.0.1')) {
        const u = new URL(serverUrl);
        inferredServerHost = `http://${u.hostname}:20128`;
      }
    } catch (_) {}

    const candidates = [
      customUrl ? customUrl.replace(/\/+$/, '') : '',
      routerHostUrl ? routerHostUrl.replace(/\/+$/, '') : '',
      inferredServerHost,
      ...LOCAL_ROUTER_HOSTS,
    ].filter(Boolean);

    for (const host of candidates) {
      const cleanHost = host.replace(/\/v1\/?$/, '').replace(/\/+$/, '');
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);
        const headers: Record<string, string> = {};
        if (apiKey) {
          headers['Authorization'] = `Bearer ${apiKey}`;
        }
        const res = await fetch(`${cleanHost}/v1/models`, {
          method: 'GET',
          headers,
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        if (res.ok) {
          return cleanHost;
        }
      } catch (_) {}
    }
    return null;
  }

  private async executeGoogleRoute(
    message: string,
    modelName: string,
    apiKey: string
  ): Promise<ChatResponse> {
    let cleanModel = modelName.replace(/^(ag|google|antigravity)\//i, '');
    if (!cleanModel || cleanModel.toLowerCase().includes('combo') || cleanModel.includes('3.7-flash-high')) {
      cleanModel = 'gemini-1.5-flash';
    }

    const candidateModels = [
      cleanModel,
      ...KNOWN_GOOGLE_MODELS.filter((m) => m !== cleanModel),
    ];

    const dynamicSkills = useSkillsStore.getState().getActiveSkillPrompts(message);
    const fullPrompt = `${DELTA_SYSTEM_PROMPT}${dynamicSkills}`;

    let lastError = '';

    for (const targetModel of candidateModels) {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${targetModel}:generateContent?key=${apiKey}`;

      const payload = {
        system_instruction: {
          parts: [{ text: fullPrompt }],
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
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!res.ok) {
          let errMsg = `HTTP ${res.status}`;
          try {
            const errJson = await res.json();
            if (errJson.error?.message) errMsg = errJson.error.message;
          } catch (_) {}
          lastError = errMsg;
          continue;
        }

        const data = await res.json();
        const reply = data.candidates?.[0]?.content?.parts?.[0]?.text || '';
        if (reply) {
          return { output: reply, response: reply, is_task: false, task_id: null };
        }
      } catch (err: any) {
        clearTimeout(timeoutId);
        lastError = err.message || 'Network timeout';
      }
    }

    throw new Error(`Google Gemini: ${lastError}`);
  }

  private async executeGatewayRoute(
    message: string,
    modelName: string,
    baseUrl: string,
    apiKey: string
  ): Promise<ChatResponse> {
    const cleanBaseUrl = (baseUrl || 'http://127.0.0.1:20128/v1').replace(/\/+$/, '');
    const url = cleanBaseUrl.endsWith('/v1') ? `${cleanBaseUrl}/chat/completions` : `${cleanBaseUrl}/v1/chat/completions`;

    const activeAgent = useSettingsStore.getState().activeAgent || 'nazza';
    const effectiveSystemPrompt = activeAgent === 'nazza' ? NAZZA_SYSTEM_PROMPT : DELTA_SYSTEM_PROMPT;
    const dynamicSkillContext = useSkillsStore.getState().getActiveSkillPrompts(message);
    const fullSystemPrompt = `${effectiveSystemPrompt}${dynamicSkillContext}`;

    const payload = {
      model: modelName || (activeAgent === 'nazza' ? 'AntigravityCombo' : 'ag/gemini-3.7-flash-high'),
      messages: [
        { role: 'system', content: fullSystemPrompt },
        { role: 'user', content: message },
      ],
      temperature: 0.7,
      stream: false,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 35000);

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!res.ok) {
        let errMsg = `Gateway Error (${res.status})`;
        try {
          const errJson = await res.json();
          if (errJson.error?.message) errMsg = errJson.error.message;
          else if (errJson.message) errMsg = errJson.message;
        } catch (_) {}
        throw new Error(errMsg);
      }

      const data = await res.json();
      const reply = data.choices?.[0]?.message?.content || data.response || data.output || '';
      return { output: reply, response: reply, is_task: false, task_id: null };
    } catch (err: any) {
      clearTimeout(timeoutId);
      throw err;
    }
  }
}

export const embedded9Router = Embedded9Router.getInstance();
