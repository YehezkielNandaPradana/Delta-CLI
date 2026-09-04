package com.deltasec.mobile.service;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.IBinder;
import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;

public class CameraMonitoringForegroundService extends Service {
    public static final String ACTION_START = "ACTION_START";
    public static final String ACTION_STOP = "ACTION_STOP";
    public static final String BROADCAST_STOP_REQUESTED = "com.deltasec.mobile.ACTION_CAMERA_STOP";
    public static final String CHANNEL_ID = "delta_camera_monitoring_service_channel";
    public static final int NOTIFICATION_ID = 9001;

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent != null) {
            String action = intent.getAction();
            if (ACTION_START.equals(action)) {
                startForegroundServiceNotification();
            } else if (ACTION_STOP.equals(action)) {
                // Broadcast to React Native to trigger clean WebRTC stop
                Intent broadcast = new Intent(BROADCAST_STOP_REQUESTED);
                broadcast.setPackage(getPackageName());
                sendBroadcast(broadcast);

                stopForeground(true);
                stopSelf();
            }
        }
        return START_NOT_STICKY; // Jangan pernah restart otomatis
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "Delta Camera Monitoring",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("Menampilkan status aktif monitoring kamera Delta");
            channel.setShowBadge(false);
            channel.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);

            NotificationManager manager = (NotificationManager) getSystemService(Context.NOTIFICATION_SERVICE);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }

    private void startForegroundServiceNotification() {
        // Intent to open Main Activity when tapping notification
        Intent launchIntent = getPackageManager().getLaunchIntentForPackage(getPackageName());
        PendingIntent pendingLaunchIntent = null;
        if (launchIntent != null) {
            int flags = Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0;
            pendingLaunchIntent = PendingIntent.getActivity(this, 0, launchIntent, flags);
        }

        // Action intent to stop monitoring directly from notification button
        Intent stopIntent = new Intent(this, CameraMonitoringForegroundService.class);
        stopIntent.setAction(ACTION_STOP);
        int flags = Build.VERSION.SDK_INT >= Build.VERSION_CODES.M ? PendingIntent.FLAG_IMMUTABLE : 0;
        PendingIntent pendingStopIntent = PendingIntent.getService(this, 1, stopIntent, flags);

        // Build native persistent foreground notification
        NotificationCompat.Builder builder = new NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("● Camera Monitoring Aktif")
            .setContentText("Kamera sedang dimonitor dari Delta Web.")
            .setSmallIcon(android.R.drawable.ic_menu_camera)
            .setContentIntent(pendingLaunchIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .addAction(android.R.drawable.ic_delete, "Hentikan", pendingStopIntent);

        Notification notification = builder.build();

        // Android 14+ (API 34) requires explicit FOREGROUND_SERVICE_TYPE_CAMERA
        if (Build.VERSION.SDK_INT >= 34) {
            startForeground(NOTIFICATION_ID, notification, ServiceInfo.FOREGROUND_SERVICE_TYPE_CAMERA);
        } else {
            startForeground(NOTIFICATION_ID, notification);
        }
    }

    @Override
    public void onDestroy() {
        stopForeground(true);
        super.onDestroy();
    }

    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
