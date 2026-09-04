package com.deltasec.mobile.service;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import androidx.annotation.NonNull;

import com.facebook.react.bridge.ReactApplicationContext;
import com.facebook.react.bridge.ReactContextBaseJavaModule;
import com.facebook.react.bridge.ReactMethod;
import com.facebook.react.bridge.Promise;
import com.facebook.react.modules.core.DeviceEventManagerModule;

public class CameraForegroundModule extends ReactContextBaseJavaModule {
    private final ReactApplicationContext reactContext;
    private BroadcastReceiver stopReceiver = null;

    public CameraForegroundModule(ReactApplicationContext reactContext) {
        super(reactContext);
        this.reactContext = reactContext;
        registerStopReceiver();
    }

    private void registerStopReceiver() {
        stopReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (CameraMonitoringForegroundService.BROADCAST_STOP_REQUESTED.equals(intent.getAction())) {
                    sendEvent("onStopRequestedFromNotification", null);
                }
            }
        };

        IntentFilter filter = new IntentFilter(CameraMonitoringForegroundService.BROADCAST_STOP_REQUESTED);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            reactContext.registerReceiver(stopReceiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            reactContext.registerReceiver(stopReceiver, filter);
        }
    }

    private void sendEvent(String eventName, Object params) {
        if (reactContext.hasActiveReactInstance()) {
            reactContext
                .getJSModule(DeviceEventManagerModule.RCTDeviceEventEmitter.class)
                .emit(eventName, params);
        }
    }

    @NonNull
    @Override
    public String getName() {
        return "CameraForegroundModule";
    }

    @ReactMethod
    public void startService(Promise promise) {
        try {
            Intent serviceIntent = new Intent(reactContext, CameraMonitoringForegroundService.class);
            serviceIntent.setAction(CameraMonitoringForegroundService.ACTION_START);

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                reactContext.startForegroundService(serviceIntent);
            } else {
                reactContext.startService(serviceIntent);
            }
            promise.resolve(true);
        } catch (Exception e) {
            promise.reject("START_SERVICE_ERROR", e.getMessage(), e);
        }
    }

    @ReactMethod
    public void stopService(Promise promise) {
        try {
            Intent serviceIntent = new Intent(reactContext, CameraMonitoringForegroundService.class);
            serviceIntent.setAction(CameraMonitoringForegroundService.ACTION_STOP);
            reactContext.startService(serviceIntent);
            promise.resolve(true);
        } catch (Exception e) {
            promise.reject("STOP_SERVICE_ERROR", e.getMessage(), e);
        }
    }

    @ReactMethod
    public void addListener(String eventName) {
        // Keep React Native Event Emitter happy
    }

    @ReactMethod
    public void removeListeners(double count) {
        // Keep React Native Event Emitter happy
    }

    @Override
    public void onCatalystInstanceDestroy() {
        super.onCatalystInstanceDestroy();
        if (stopReceiver != null) {
            try {
                reactContext.unregisterReceiver(stopReceiver);
            } catch (Exception ignored) {}
            stopReceiver = null;
        }
    }
}
