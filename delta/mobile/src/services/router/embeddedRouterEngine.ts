/**
 * Embedded 9Router Engine for Delta Mobile
 * Provides zero-server, zero-manual-setup in-app AI model routing.
 * Automatically runs on app launch inside React Native/Expo.
 */

import { AntigravityAccount } from '../../types/cloud';
import { ChatResponse } from '../api/chatApi';
import { DELTA_SYSTEM_PROMPT } from '../api/directCloudClient';

export interface EmbeddedRouterStatus {
  running: boolean;
  version: string;
  mode: 'embedded' | 'remote';
  activeProviders: string[];
  activeCombo: string;
  uptime_seconds: number;
}

const startTime = Date.now();

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
      version: '9router-embedded-v2.5',
      mode: 'embedded',
      activeProviders: ['antigravity', 'google', 'opencode', 'deepseek'],
      activeCombo: 'AntigravityCombo',
      uptime_seconds: Math.floor((Date.now() - startTime) / 1000),
    };
  }

  /**
   * Route any combo model or custom provider model directly to best endpoint
   */
  public async routeCompletion(
    message: string,
    modelName: string,
    account?: AntigravityAccount
  ): Promise<ChatResponse> {
    const rawKey = account?.apiKey?.trim() || '';
    const customBaseUrl = (account?.baseUrl || '').trim();

    // 1. If user connects to Termux 9Router (localhost / 127.0.0.1 on port 20128)
    if (
      customBaseUrl.includes('127.0.0.1') ||
      customBaseUrl.includes('localhost') ||
      customBaseUrl.includes(':20128')
    ) {
      return this.executeGatewayRoute(message, modelName, customBaseUrl, rawKey);
    }

    // 2. If user provided a Google AI Studio key (or no key yet with Google fallback)
    if (rawKey.startsWith('AIzaSy') || !customBaseUrl) {
      return this.executeGoogleRoute(message, modelName, rawKey);
    }

    // 3. OpenAI / Antigravity Cloud Gateway route
    return this.executeGatewayRoute(message, modelName, customBaseUrl, rawKey);
  }

  private async executeGoogleRoute(
    message: string,
    modelName: string,
    apiKey: string
  ): Promise<ChatResponse> {
    if (!apiKey) {
      throw new Error(
        '9Router Embedded: API Key belum diisi. Silakan tambahkan API Key di menu Settings.'
      );
    }

    // Curated model priorities for Google AI Studio
    const candidateModels = [
      'gemini-1.5-flash',
      'gemini-1.5-flash-latest',
      'gemini-1.5-pro',
      'gemini-1.5-pro-latest',
      'gemini-3.6-flash',
    ];

    let lastError = '';

    for (const targetModel of candidateModels) {
      const url = `https://generativelanguage.googleapis.com/v1beta/models/${targetModel}:generateContent?key=${apiKey}`;

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
          continue; // Try next candidate in 9Router chain
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

    throw new Error(`9Router Google Route Failed: ${lastError}`);
  }

  private async executeGatewayRoute(
    message: string,
    modelName: string,
    baseUrl: string,
    apiKey: string
  ): Promise<ChatResponse> {
    const cleanBaseUrl = (baseUrl || 'https://api.antigravity.ai/v1').replace(/\/+$/, '');
    const url = `${cleanBaseUrl}/chat/completions`;

    const payload = {
      model: modelName || 'ag/gemini-3.7-flash-high',
      messages: [
        { role: 'system', content: DELTA_SYSTEM_PROMPT },
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
